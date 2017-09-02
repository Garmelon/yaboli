import asyncio
from connection import Connection
import utils

class Room:
	ROOM_FORMAT = "wss://euphoria.io/room/{}/ws"
	HUMAN_FORMAT = f"{ROOM_FORMAT}?h=1"
	
	def __init__(self, roomname, controller, human=False, cookie=None):
		self.roomname = roomname
		self.controller = controller
		self.human = human
		self.cookie = cookie
		
		# Keeps track of sessions, but not messages, since they might be dealt
		# with differently by different controllers.
		# If you need to keep track of messages, use utils.Log.
		self.session = None
		self.account = None
		self.listing = utils.Listing()
		
		# Various room information
		self.account_has_access = None
		self.account_email_verified = None
		self.room_is_private = None
		self.version = None # the version of the code being run and served by the server
		self.pm_with_nick = None
		self.pm_with_user_id = None
		
		self._callbacks = {}
		self._add_callbacks()
		
		if human:
			url = self.HUMAN_FORMAT.format(self.roomname)
		else:
			url = self.ROOM_FORMAT.format(self.roomname)
		self._conn = Connection(url, self._handle_packet, self.cookie)
	
	async def run(self):
		await self._conn.run()
	
	async def stop(self):
		await self._conn.stop()
	
	# CATEGORY: SESSION COMMANDS
	
	async def auth(self, atype, passcode):
		pass # TODO
	
	async def ping_reply(self, time):
		"""
		From api.euphoria.io:
		The ping command initiates a client-to-server ping. The server will
		send back a ping-reply with the same timestamp as soon as possible.
		
		ping-reply is a response to a ping command or ping-event.
		"""
		
		data = {"time": time}
		await self._conn.send("ping-reply", data, await_response=False)
	
	# CATEGORY: CHAT ROOM COMMANDS
	
	async def get_message(self, message_id):
		pass # TODO
	
	async def log(self, n, before=None):
		pass # TODO
	
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
		
		response = await self._conn.send("nick", data)
		self._check_for_errors(response)
		
		session_id = response.get("session_id")
		user_id = response.get("id")
		from_nick = response.get("from")
		to_nick = response.get("to")
		
		self.session.nick = to_nick
		
		return session_id, user_id, from_nick, to_nick
	
	async def pm_initiate(self, user_id):
		pass # TODO
	
	async def send(self, content, parent=None):
		"""
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
		
		response = await self._conn.send("send", data)
		self._check_for_errors(response)
		
		message = utils.Message.from_dict(response.get("data"))
		return message
	
	async def who(self):
		pass # TODO
	
	# CATEGORY: ACCOUNT COMMANDS
	# NYI, and probably never will
	
	# CATEGORY: ROOM HOST COMMANDS
	# NYI, and probably never will
	
	# CATEGORY: STAFF COMMANDS
	# NYI, and probably never will
	
	
	
	# All the private functions for dealing with stuff
	
	def _add_callbacks(self):
		self._callbacks["bounce-event"] = self._handle_bounce
		self._callbacks["disconnect-event"] = self._handle_disconnect
		self._callbacks["hello-event"] = self._handle_hello
		self._callbacks["join-event"] = self._handle_join
		self._callbacks["login-event"] = self._handle_login
		self._callbacks["logout-event"] = self._handle_logout
		self._callbacks["network-event"] = self._handle_network
		self._callbacks["nick-event"] = self._handle_nick
		self._callbacks["edit-message-event"] = self._handle_edit_message
		self._callbacks["part-event"] = self._handle_part
		self._callbacks["ping-event"] = self._handle_ping
		self._callbacks["pm-initiate-event"] = self._handle_pm_initiate
		self._callbacks["send-event"] = self._handle_send
		self._callbacks["snapshot-event"] = self._handle_snapshot
	
	async def _handle_packet(self, packet):
		self._check_for_errors(packet)
		
		ptype = packet.get("type")
		callback = self._callbacks.get(ptype)
		if callback:
			try:
				await callback(packet)
			except asyncio.CancelledError as e:
				# TODO: log error
				print("HEHEHEHEY, CANCELLEDERROR", e)
				pass
	
	def _check_for_errors(self, packet):
		# TODO: log throttled
		
		if "error" in packet:
			raise utils.ResponseError(response.get("error"))
	
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
		self.session = utils.Session.from_dict(data.get("session"))
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
		session = utils.Session.from_dict(data)
		
		# update self.listing
		self.listing.add(session)
		
		await self.controller.on_join(session)
	
	async def _handle_login(self, packet):
		pass # TODO
	
	async def _handle_logout(self, packet):
		pass # TODO
	
	async def _handle_network(self, packet):
		pass # TODO
	
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
		pass # TODO
	
	async def _handle_part(self, packet):
		"""
		From api.euphoria.io:
		A part-event indicates a session just disconnected from the room.
		"""
		
		data = packet.get("data")
		session = utils.Session.from_dict(data)
		
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
		pass # TODO
	
	async def _handle_send(self, packet):
		"""
		From api.euphoria.io:
		A send-event indicates a message received by the room from another
		session.
		"""
		
		data = packet.get("data")
		message = utils.Message.from_dict(data)
		
		await self.controller.on_send(message)
	
	async def _handle_snapshot(self, packet):
		"""
		From api.euphoria.io:
		A snapshot-event indicates that a session has successfully joined a
		room. It also offers a snapshot of the room’s state and recent history.
		"""
		
		data = packet.get("data")
		
		sessions = [utils.Session.from_dict(d) for d in data.get("listing")]
		messages = [utils.Message.from_dict(d) for d in data.get("log")]
		
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
