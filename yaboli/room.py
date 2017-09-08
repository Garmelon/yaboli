import asyncio
import logging
from .callbacks import *
from .connection import *
from .utils import *

logger = logging.getLogger(__name__)
__all__ = ["Room"]



class Room:
	"""
	This class represents a connection to a room. This basically means that one
	room instance means one nick on the nick list.
	
	It's purpose is to provide a higher-level way of interacting with a room to
	a controller. This includes converting packets received from the server to
	utility classes where possible, or keeping track of current room state like
	the client's nick.
	It does not keep track of the room's messages, as keeping (or not keeping)
	messages is highly application-dependent. If needed, messages can be kept
	using the utils.Log class.
	
	Room implements all commands necessary for creating bots. For now, the
	human flag should always be False, and the cookie None.
	It also "attaches" to a controller and calls the corresponding functions
	when it receives events from the server
	
	When connection is lost while the room is running, it will attempt to
	reconnect a few times. Loss of connection is determined by self._conn.
	"""
	
	ROOM_FORMAT = "wss://euphoria.io/room/{}/ws"
	HUMAN_FORMAT = f"{ROOM_FORMAT}?h=1"
	
	def __init__(self, roomname, controller, human=False, cookie=None):
		"""
		Create a room. To connect to the room and start a run task that listens
		to packets on the connection, use connect().
		
		roomname   - name of the room to connect to, without a "&" in front
		controller - the controller which should be notified of events
		human      - currently not implemented, should be False
		cookie     - currently not implemented, should be None
		"""
		
		self.roomname = roomname
		self.controller = controller
		self.human = human
		self.cookie = cookie
		
		# Keeps track of sessions, but not messages, since they might be dealt
		# with differently by different controllers.
		# If you need to keep track of messages, use utils.Log.
		self.session = None
		self.account = None
		self.listing = Listing()
		
		# Various room information
		self.account_has_access = None
		self.account_email_verified = None
		self.room_is_private = None
		self.version = None # the version of the code being run and served by the server
		self.pm_with_nick = None
		self.pm_with_user_id = None
		
		self._callbacks = Callbacks()
		self._add_callbacks()
		
		self._stopping = False
		self._runtask = None
		
		if human:
			url = self.HUMAN_FORMAT.format(self.roomname)
		else:
			url = self.ROOM_FORMAT.format(self.roomname)
		self._conn = Connection(url, self._handle_packet, self.cookie)
	
	async def connect(self, max_tries=10, delay=60):
		"""
		runtask = await connect(max_tries, delay)
		
		Attempts to connect to the room once and returns a task running
		self._run, if successful, otherwise None. This can be used to detect if
		a room exists.
		
		The max_tries and delay parameters are passed on to self._run:
		max_tries - maximum number of reconnect attempts before stopping
		delay     - time (in seconds) between reconnect attempts
		"""
		
		task = await self._conn.connect(max_tries=1)
		if task:
			self._runtask = asyncio.ensure_future(self._run(task, max_tries=max_tries, delay=delay))
			return self._runtask
	
	async def _run(self, task, max_tries=10, delay=60):
		"""
		await _run(max_tries, delay)
		
		Run and reconnect when the connection is lost or closed, unless
		self._stopping is set to True.
		For an explanation of the parameters, see self.connect.
		"""
		
		while not self._stopping:
			if task.done():
				task = await self._conn.connect(max_tries=max_tries, delay=delay)
				if not task:
					return
			
			await task
			await self.controller.on_disconnected()
		
		self.stopping = False
	
	async def stop(self):
		"""
		await stop()
		
		Close the connection to the room without reconnecting.
		"""
		
		self._stopping = True
		await self._conn.stop()
		
		if self._runtask:
			await self._runtask
	
	
	
	# CATEGORY: SESSION COMMANDS
	
	async def auth(self, atype, passcode=None):
		"""
		success, reason=None = await auth(atype, passcode=None)
		
		  From api.euphoria.io:
		The auth command attempts to join a private room. It should be sent in
		response to a bounce-event at the beginning of a session.
		
		The auth-reply packet reports whether the auth command succeeded.
		"""
		
		data = {"type": atype}
		if passcode:
			data["passcode"] = passcode
			
		response = await self._send_packet("auth", data)
		rdata = response.get("data")
		
		success = rdata.get("success")
		reason = rdata.get("reason", None)
		return success, reason
	
	async def ping_reply(self, time):
		"""
		await ping_reply(time)
		
		  From api.euphoria.io:
		The ping command initiates a client-to-server ping. The server will
		send back a ping-reply with the same timestamp as soon as possible.
		
		ping-reply is a response to a ping command or ping-event.
		"""
		
		data = {"time": time}
		await self._conn.send("ping-reply", data, await_response=False)
	
	# CATEGORY: CHAT ROOM COMMANDS
	
	async def get_message(self, message_id):
		"""
		message = await get_message(message_id)
		
		  From api.euphoria.io:
		The get-message command retrieves the full content of a single message
		in the room.
		
		get-message-reply returns the message retrieved by get-message.
		"""
		
		data = {"id": message_id}
		
		response = await self._send_packet("get-message", data)
		rdata = response.get("data")
		
		message = Message.from_dict(rdata)
		return message
	
	async def log(self, n, before=None):
		"""
		log, before=None = await log(n, before=None)
		
		  From api.euphoria.io:
		The log command requests messages from the room’s message log. This can
		be used to supplement the log provided by snapshot-event (for example,
		when scrolling back further in history).
		
		The log-reply packet returns a list of messages from the room’s message
		"""
		
		data = {"n": n}
		if before:
			data["before"] = before
			
		response = await self._send_packet("log", data)
		rdata = response.get("data")
		
		messages = [Message.from_dict(d) for d in rdata.get("log")]
		before = rdata.get("before", None)
		return messages, before
	
	async def nick(self, name):
		"""
		session_id, user_id, from_nick, to_nick = await nick(name)
		
		  From api.euphoria.io:
		The nick command sets the name you present to the room. This name
		applies to all messages sent during this session, until the nick
		command is called again.
		
		nick-reply confirms the nick command. It returns the session’s former
		and new names (the server may modify the requested nick).
		"""
		
		data = {"name": name}
		
		response = await self._send_packet("nick", data)
		rdata = response.get("data")
		
		session_id = rdata.get("session_id")
		user_id = rdata.get("id")
		from_nick = rdata.get("from")
		to_nick = rdata.get("to")
		
		# update self.session
		self.session.nick = to_nick
		
		return session_id, user_id, from_nick, to_nick
	
	async def pm_initiate(self, user_id):
		"""
		pm_id, to_nick = await pm_initiate(user_id)
		
		  From api.euphoria.io:
		The pm-initiate command constructs a virtual room for private messaging
		between the client and the given UserID.
		
		The pm-initiate-reply provides the PMID for the requested private
		messaging room.
		"""
		
		data = {"user_id": user_id}
		
		response = await self._send_packet("pm-initiate", data)
		rdata = response.get("data")
		
		pm_id = rdata.get("pm_id")
		to_nick = rdata.get("to_nick")
		return pm_id, to_nick
	
	async def send(self, content, parent=None):
		"""
		message = await send(content, parent=None)
		
		  From api.euphoria.io:
		The send command sends a message to a room. The session must be
		successfully joined with the room. This message will be broadcast to
		all sessions joined with the room.
		
		If the room is private, then the message content will be encrypted
		before it is stored and broadcast to the rest of the room.
		
		The caller of this command will not receive the corresponding
		send-event, but will receive the same information in the send-reply.
		"""
		
		data = {"content": content}
		if parent:
			data["parent"] = parent
		
		response = await self._send_packet("send", data)
		rdata = response.get("data")
		
		message = Message.from_dict(rdata)
		return message
	
	async def who(self):
		"""
		sessions = await who()
		
		  From api.euphoria.io:
		The who command requests a list of sessions currently joined in the
		room.
		
		The who-reply packet lists the sessions currently joined in the room.
		"""
		
		response = await self._send_packet("who")
		rdata = response.get("data")
		
		sessions = [Session.from_dict(d) for d in rdata.get("listing")]
		
		# update self.listing
		self.listing = Listing()
		for session in sessions:
			self.listing.add(session)
		
		return sessions
	
	# CATEGORY: ACCOUNT COMMANDS
	# NYI, and probably never will
	
	# CATEGORY: ROOM HOST COMMANDS
	# NYI, and probably never will
	
	# CATEGORY: STAFF COMMANDS
	# NYI, and probably never will
	
	
	
	# All the private functions for dealing with stuff
	
	def _add_callbacks(self):
		"""
		_add_callbacks()
		
		Adds the functions that handle server events to the callbacks for that
		event.
		"""
		
		self._callbacks.add("bounce-event", self._handle_bounce)
		self._callbacks.add("disconnect-event", self._handle_disconnect)
		self._callbacks.add("hello-event", self._handle_hello)
		self._callbacks.add("join-event", self._handle_join)
		self._callbacks.add("login-event", self._handle_login)
		self._callbacks.add("logout-event", self._handle_logout)
		self._callbacks.add("network-event", self._handle_network)
		self._callbacks.add("nick-event", self._handle_nick)
		self._callbacks.add("edit-message-event", self._handle_edit_message)
		self._callbacks.add("part-event", self._handle_part)
		self._callbacks.add("ping-event", self._handle_ping)
		self._callbacks.add("pm-initiate-event", self._handle_pm_initiate)
		self._callbacks.add("send-event", self._handle_send)
		self._callbacks.add("snapshot-event", self._handle_snapshot)
	
	async def _send_packet(self, *args, **kwargs):
		"""
		reply_packet = await _send_packet(*args, **kwargs)
		
		Like self._conn.send, but checks for an error on the packet and raises
		the corresponding exception.
		"""
		
		response = await self._conn.send(*args, **kwargs)
		self._check_for_errors(response)
		
		return response
	
	async def _handle_packet(self, packet):
		"""
		await _handle_packet(packet)
		
		Call the correct callbacks to deal with packet.
		
		This function catches CancelledErrors and instead displays an info so
		the console doesn't show stack traces when a bot loses connection.
		"""
		
		self._check_for_errors(packet)
		
		ptype = packet.get("type")
		try:
			await self._callbacks.call(ptype, packet)
		except asyncio.CancelledError as e:
			logger.info(f"&{self.roomname}: Callback of type {ptype!r} cancelled.")
			#raise # not necessary?
	
	def _check_for_errors(self, packet):
		"""
		_check_for_errors(packet)
		
		Checks for an error on the packet and raises the corresponding
		exception.
		"""
		
		if packet.get("throttled", False):
			logger.warn(f"&{self.roomname}: Throttled for reason: {packet.get('throttled_reason', 'no reason')!r}")
		
		if "error" in packet:
			raise ResponseError(packet.get("error"))
	
	async def _handle_bounce(self, packet):
		"""
		  From api.euphoria.io:
		A bounce-event indicates that access to a room is denied.
		"""
		
		data = packet.get("data")
		
		await self.controller.on_bounce(
			reason=data.get("reason", None),
			auth_options=data.get("auth_options", None),
			agent_id=data.get("agent_id", None),
			ip=data.get("ip", None)
		)
	
	async def _handle_disconnect(self, packet):
		"""
		  From api.euphoria.io:
		A disconnect-event indicates that the session is being closed. The
		client will subsequently be disconnected.
		
		If the disconnect reason is “authentication changed”, the client should
		immediately reconnect.
		"""
		
		data = packet.get("data")
		
		await self.controller.on_disconnect(data.get("reason"))
	
	async def _handle_hello(self, packet):
		"""
		  From api.euphoria.io:
		A hello-event is sent by the server to the client when a session is
		started. It includes information about the client’s authentication and
		associated identity.
		"""
		
		data = packet.get("data")
		self.session = Session.from_dict(data.get("session"))
		self.room_is_private = data.get("room_is_private")
		self.version = data.get("version")
		self.account = data.get("account", None)
		self.account_has_access = data.get("account_has_access", None)
		self.account_email_verified = data.get("account_email_verified", None)
		
		await self.controller.on_hello(
			data.get("id"),
			self.session,
			self.room_is_private,
			self.version,
			account=self.account,
			account_has_access=self.account_has_access,
			account_email_verified=self.account_email_verified
		)
	
	async def _handle_join(self, packet):
		"""
		  From api.euphoria.io:
		A join-event indicates a session just joined the room.
		"""
		
		data = packet.get("data")
		session = Session.from_dict(data)
		
		# update self.listing
		self.listing.add(session)
		
		await self.controller.on_join(session)
	
	async def _handle_login(self, packet):
		"""
		  From api.euphoria.io:
		The login-event packet is sent to all sessions of an agent when that
		agent is logged in (except for the session that issued the login
		command).
		"""
		
		data = packet.get("data")
		
		await self.controller.on_login(data.get("account_id"))
	
	async def _handle_logout(self, packet):
		"""
		  From api.euphoria.io:
		The logout-event packet is sent to all sessions of an agent when that
		agent is logged out (except for the session that issued the logout
		command).
		"""
		
		await self.controller.on_logout()
	
	async def _handle_network(self, packet):
		"""
		  From api.euphoria.io:
		A network-event indicates some server-side event that impacts the
		presence of sessions in a room.
		
		If the network event type is partition, then this should be treated as
		a part-event for all sessions connected to the same server id/era
		combo.
		"""
		
		data = packet.get("data")
		server_id = data.get("server_id")
		server_era = data.get("server_era")
		
		# update self.listing
		self.listing.remove_combo(server_id, server_era)
		
		await self.controller.on_network(server_id, server_era)
	
	async def _handle_nick(self, packet):
		"""
		  From api.euphoria.io:
		nick-event announces a nick change by another session in the room.
		"""
		
		data = packet.get("data")
		session_id = data.get("session_id")
		to_nick = data.get("to")
		
		# update self.listing
		session = self.listing.by_sid(session_id)
		if session:
			session.nick = to_nick
		
		await self.controller.on_nick(
			session_id,
			data.get("id"),
			data.get("from"),
			to_nick
		)
	
	async def _handle_edit_message(self, packet):
		"""
		  From api.euphoria.io:
		An edit-message-event indicates that a message in the room has been
		modified or deleted. If the client offers a user interface and the
		indicated message is currently displayed, it should update its display
		accordingly.
		
		The event packet includes a snapshot of the message post-edit.
		"""
		
		data = packet.get("data")
		message = Message.from_dict(data)
		
		await self.controller.on_edit_message(
			data.get("edit_id"),
			message
		)
	
	async def _handle_part(self, packet):
		"""
		  From api.euphoria.io:
		A part-event indicates a session just disconnected from the room.
		"""
		
		data = packet.get("data")
		session = Session.from_dict(data)
		
		# update self.listing
		self.listing.remove(session.session_id)
		
		await self.controller.on_part(session)
	
	async def _handle_ping(self, packet):
		"""
		  From api.euphoria.io:
		A ping-event represents a server-to-client ping. The client should send
		back a ping-reply with the same value for the time field as soon as
		possible (or risk disconnection).
		"""
		
		data = packet.get("data")
		
		await self.controller.on_ping(
			data.get("time"),
			data.get("next")
		)
	
	async def _handle_pm_initiate(self, packet):
		"""
		  From api.euphoria.io:
		The pm-initiate-event informs the client that another user wants to
		chat with them privately.
		"""
		
		data = packet.get("data")
		
		await self.controller.on_pm_initiate(
			data.get("from"),
			data.get("from_nick"),
			data.get("from_room"),
			data.get("pm_id")
		)
	
	async def _handle_send(self, packet):
		"""
		  From api.euphoria.io:
		A send-event indicates a message received by the room from another
		session.
		"""
		
		data = packet.get("data")
		message = Message.from_dict(data)
		
		await self.controller.on_send(message)
	
	async def _handle_snapshot(self, packet):
		"""
		  From api.euphoria.io:
		A snapshot-event indicates that a session has successfully joined a
		room. It also offers a snapshot of the room’s state and recent history.
		"""
		
		data = packet.get("data")
		
		sessions = [Session.from_dict(d) for d in data.get("listing")]
		messages = [Message.from_dict(d) for d in data.get("log")]
		
		# update self.listing
		for session in sessions:
			self.listing.add(session)
		
		self.session.nick = data.get("nick", None)
		
		self.pm_with_nick = data.get("pm_with_nick", None),
		self.pm_with_user_id = data.get("pm_with_user_id", None)
		
		await self.controller.on_connected()
		
		await self.controller.on_snapshot(
			data.get("identity"),
			data.get("session_id"),
			self.version,
			sessions, # listing
			messages, # log
			nick=self.session.nick,
			pm_with_nick=self.pm_with_nick,
			pm_with_user_id=self.pm_with_user_id
		)
