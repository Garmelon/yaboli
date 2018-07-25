__all__ == ["Room", "Inhabitant"]


class Room:
	"""
	TODO
	"""

	def __init__(self, roomname, inhabitant, password=None, human=False, cookiejar=None):
		# TODO: Connect to room etc.
		# TODO: Deal with room/connection states of:
		# disconnected connecting, fast-forwarding, connected

		self._inhabitant = inhabitant

		# Room info (all fields readonly!)
		self.roomname = roomname
		self.session = None
		self.account = None
		self.listing = None # TODO
		self.account_has_access = None
		self.account_email_verified = None
		self.room_is_private = None
		self.version = None # the version of the code being run and served by the server
		self.pm_with_nick = None
		self.pm_with_user_id = None

		#asyncio.create_task(self._run())

	async def exit(self):
		pass

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

	async def _receive_packet(self, ptype, data, error, throttled):
		pass # TODO

	async def _disconnected(self):
		pass # TODO

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
		pass

# REST OF THE IMPLEMENTATION

	async def _run(self):
		pass

	async def _send_while_connected(*args, **kwargs):
		while True:
			try:
				await self.connected()
				if not self._status != Room._CONNECTED: continue # TODO: Figure out a good solution
				return await self._connection.send(*args, **kwargs)
			except RoomDisconnected:
				pass # Just try again


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

	async def pm(self, room, from_uid, from_nick, from_room, pm_id):
		pass
