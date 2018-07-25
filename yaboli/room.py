from .connection import *
from .exceptions import *
from .utils import *


__all__ == ["Room", "Inhabitant"]


class Room:
	"""
	TODO
	"""

	CONNECTED = 1
	DISCONNECTED = 2
	EXITED = 3

	def __init__(self, roomname, inhabitant, password=None, human=False, cookiejar=None):
		# TODO: Connect to room etc.
		# TODO: Deal with room/connection states of:
		# disconnected connecting, fast-forwarding, connected

		# Room info (all fields readonly!)
		self.roomname = roomname
		self.password = password
		self.human = human

		self.session = None
		self.account = None
		self.listing = Listing()

		self.account_has_access = None
		self.account_email_verified = None
		self.room_is_private = None
		self.version = None # the version of the code being run and served by the server
		self.pm_with_nick = None
		self.pm_with_user_id = None

		self._inhabitant = inhabitant
		self._status = Room.DISCONNECTED

		# TODO: Allow for all parameters of Connection() to be specified in Room().
		self._connection = Connection(
			self.format_room_url(self.roomname, human=self.human),
			self._receive_packet,
			self._disconnected,
			cookiejar
		)

	async def exit(self):
		self._status = Room.EXITED
		await self._connection.stop()

# ROOM COMMANDS
# These always return a response from the server.
# If the connection is lost while one of these commands is called,
# the command will retry once the bot has reconnected.

	async def get_message(self, mid):
		pass

	async def log(self, n, before_mid=None):
		pass

	async def nick(self, nick):
		pass

	async def pm(self, uid):
		pass

	async def send(self, content, parent_mid=None):
		"""
		Send a message to the room.
		See http://api.euphoria.io/#send
		"""

		if parent_mid:
			data = await self._send_while_connected(
				"send",
				content=content,
				parent=parent_mid
			)
		else:
			data = await self._send_while_connected(
				"send",
				content=content
			)

		return Message.from_dict(data)

	async def who(self):
		pass

# COMMUNICATION WITH CONNECTION

	async def _disconnected(self):
		# While disconnected, keep the last known session info, listing etc.
		# All of this is instead reset when the hello/snapshot events are received.
		self.status = Room.DISCONNECTED
		self._connected_future = asyncio.Future()

		await self._inhabitant.disconnected(self)

	async def _receive_packet(self, ptype, data, error, throttled):
		# Ignoring errors and throttling for now
		functions = {
			"bounce-event":       self._event_bounce,
			#"disconnect-event":   self._event_disconnect, # Not important, can ignore
			"hello-event":        self._event_hello,
			"join-event":         self._event_join,
			#"login-event":        self._event_login,
			#"logout-event":       self._event_logout,
			"network-event":      self._event_network,
			"nick-event":         self._event_nick,
			#"edit-message-event": self._event_edit_message,
			"part-event":         self._event_part,
			"ping-event":         self._event_ping,
			"pm-initiate-event":  self._event_pm_initiate,
			"send-event":         self._event_send,
			"snapshot-event":     self._event_snapshot,
		}

		function = functions.get(ptype)
		if function:
			await function(data)

	async def _event_bounce(self, data):
		if self.password is not None:
			try:
				response = await self._connection.send("auth", type=passcode, passcode=self.password)
				rdata = response.get("data")
				success = rdata.get("success")
				if not success:
					reason = rdata.get("reason")
					raise AuthenticationRequired(f"Could not join &{self.roomname}: {reason}")
			except ConnectionClosed:
				pass
		else:
			raise AuthenticationRequired(f"&{self.roomname} is password locked but no password was given")

	async def _event_hello(self, data):
		self.session = Session.from_dict(data.get("session"))
		self.room_is_private = = data.get("room_is_private")
		self.version = data.get("version")
		self.account = data.get("account", None)
		self.account_has_access = data.get("account_has_access", None)
		self.account_email_verified = data.get("account_email_verified", None)

	async def _event_join(self, data):
		session = Session.from_dict(data)
		self.listing.add(session)
		await self._inhabitant.join(self, session)

	async def _event_network(self, data):
		server_id = data.get("server_id")
		server_era = data.get("server_era")

		sessions = self.listing.remove_combo(server_id, server_era)
		for session in sessions:
			await self._inhabitant.part(self, session)

	async def _event_nick(self, data):
		sid = data.get("session_id")
		uid = data.get("user_id")
		from_nick = data.get("from")
		to_nick = data.get("to")

		session = self.listing.by_sid(sid)
		if session:
			session.nick = to_nick

		await self._inhabitant.nick(self, sid, uid, from_nick, to_nick)

	async def _event_part(self, data):
		session = Session.from_dict(data)
		self.listing.remove(session.sid)
		await self._inhabitant.part(self, session)

	async def _event_ping(self, data):
		try:
			self._connection.send()
		except exceptions.ConnectionClosed:
			pass

	async def _event_pm_initiate(self, data):
		from_uid = data.get("from")
		from_nick = data.get("from_nick")
		from_room = data.get("from_room")
		pm_id = data.get("pm_id")

		await self._inhabitant.pm(self, from_uid, from_nick, from_room, pm_id)

	async def _event_send(self, data):
		pass # TODO X
		# TODO: Figure out a way to bring fast-forwarding into this

	async def _event_snapshot(self, data):
		# update listing
		self.listing = Listing()
		sessions = [Session.from_dict(d) for d in data.get("listing")]
		for session in sessions:
			self.listing.add(session)

		# update (and possibly set) nick
		new_nick = data.get("nick", None)
		if self.session:
			prev_nick = self.session.nick
			if new_nick != prev_nick:
				self.nick(prev_nick)
		self.session.nick = new_nick

		# update more room info
		self.pm_with_nick = data.get("pm_with_nick", None),
		self.pm_with_user_id = data.get("pm_with_user_id", None)

		# Now, we're finally connected again!
		self.status = Room.CONNECTED
		if not self._connected_future.done(): # should always be True, I think
			self._connected_future.set_result(None)

		# Let's let the inhabitant know.
		log = [Message.from_dict(m) for m in data.get("log")]
		await self._inhabitant.connected(self, log)

		# TODO: Figure out a way to bring fast-forwarding into this
		# Should probably happen where this comment is

# SOME USEFUL PUBLIC METHODS

	@staticmethod
	def format_room_url(roomname, private=False, human=False):
		if private:
			roomname = f"pm:{roomname}"

		url = f"wss://euphoria.io/room/{roomname}/ws"

		if human:
			url = f"{url}?h=1"

		return url

	async def connected(self):
		await self._connected_future

# REST OF THE IMPLEMENTATION

	async def _send_while_connected(*args, **kwargs):
		while True:
			if self._status == Room.CLOSED:
				raise RoomClosed()

			try:
				await self.connected()
				return await self._connection.send(*args, **kwargs)
			except ConnectionClosed:
				pass # just try again


class Inhabitant:
	"""
	TODO
	"""

# ROOM EVENTS
# These functions are called by the room when something happens.
# They're launched via asyncio.create_task(), so they don't block execution of the room.
# Just overwrite the events you need (make sure to keep the arguments the same though).

	async def disconnected(self, room):
		pass

	async def connected(self, room, log):
		pass

	async def join(self, room, session):
		pass

	async def part(self, room, session):
		pass

	async def nick(self, room, sid, uid, from_nick, to_nick):
		pass

	async def send(self, room, message):
		pass

	async def fast_forward(self, room, message):
		pass

	async def pm(self, room, from_uid, from_nick, from_room, pm_id):
		pass
