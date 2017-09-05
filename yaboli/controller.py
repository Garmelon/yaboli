import asyncio
import logging
from .room import Room

logger = logging.getLogger(__name__)
__all__ = ["Controller"]



class Controller:
	"""
	Callback order:
	
	on_start               - self.room not available
	while running:
		<connects to room>
		on_ping            - always possible (until on_disconnected)
		on_bounce          - self.room only session
		on_hello           - self.room only session
		<authenticated, access to room>
		on_connected       - self.room session and chat room (fully connected)
		on_snapshot        - self.room session and chat room
		<other callbacks>  - self.room session and chat room
		<leaving room>
		on_disconnected    - self.room not connected to room any more
	on_stop                - self.room not available
	
	"""
	
	def __init__(self, nick, human=False, cookie=None):
		"""
		roomname  - name of room to connect to
		human     - whether the human flag should be set on connections
		cookie    - cookie to use in HTTP request, if any
		"""
		self.nick = nick
		self.human = human
		self.cookie = cookie
		
		self.roomname = "test"
		self.password = None
		
		self.room = None
		self._connect_result = None
	
	def _create_room(self, roomname):
		return Room(roomname, self, human=self.human, cookie=self.cookie)
	
	def _set_connect_result(self, result):
		logger.debug(f"Attempting to set connect result to {result}")
		if self._connect_result and not self._connect_result.done():
			logger.debug(f"Setting connect result to {result}")
			self._connect_result.set_result(result)
	
	async def connect(self, roomname, password=None, timeout=10):
		"""
		task, reason = await connect(roomname, password=None, timeout=10)
		
		Connect to a room and authenticate, if necessary.
		
		roomname - name of the room to connect to
		password - password for the room, if needed
		timeout  - wait this long for a reply from the server
		
		Returns:
		task     - the task running the bot, or None on failure
		reason   - the reason for failure
		  "no room"        = could not establish connection, room doesn't exist
		  "auth option"    = can't authenticate with a password
		  "no password"    = password needed to connect to room
		  "wrong password" = password given does not work
		  "disconnected"   = connection closed before client could access the room
		  "success"        = no failure
		"""
		
		logger.info(f"Attempting to connect to &{roomname}")
		
		# make sure nothing is running any more
		try:
			await self.stop()
		except asyncio.CancelledError:
			logger.error("Calling connect from the controller itself.")
			raise
		
		self.password = password
		self.room = self._create_room(roomname)
		
		# prepare for if connect() is successful
		self._connect_result = asyncio.Future()
		
		# attempt to connect to the room
		task = await self.room.connect()
		if not task:
			logger.warn(f"Could not connect to &{roomname}.")
			self.room = None
			return None, "no room"
		
		# connection succeeded, now we need to know whether we can log in
		# wait for success/authentication/disconnect
		# TODO: add a timeout
		await self._connect_result
		result = self._connect_result.result()
		logger.debug(f"&{roomname}._connect_result: {result!r}")
		
		# deal with result
		if result == "success":
			logger.info(f"Successfully connected to &{roomname}.")
			return task, result
		else: # not successful for some reason
			logger.warn(f"Could not join &{roomname}: {result!r}")
			await self.stop()
			return None, result
	
	async def stop(self):
		if self.room:
			logger.info(f"@{self.nick}: Stopping")
			await self.room.stop()
			logger.debug(f"@{self.nick}: Stopped. Deleting room")
			self.room = None
	
	async def set_nick(self, nick):
		if nick != self.nick:
			_, _, _, to_nick = await self.room.nick(nick)
			self.nick = to_nick
			
			if to_nick != nick:
				logger.warn(f"&{self.room.roomname}: Could not set nick to {nick!r}, set to {to_nick!r} instead.")
	
	async def on_connected(self):
		"""
		Client has successfully (re-)joined the room.
		
		Use: Actions that are meant to happen upon (re-)connecting to a room,
		     such as resetting the message history.
		"""
		
		self._set_connect_result("success")
	
	async def on_disconnected(self):
		"""
		Client has disconnected from the room.
		
		This is the last time the old self.room can be accessed.
		Use: Reconfigure self before next connection.
		     Need to store information from old room?
		"""
		
		logger.debug(f"on_disconnected: self.room is {self.room}")
		self._set_connect_result("disconnected")
	
	async def on_bounce(self, reason=None, auth_options=[], agent_id=None, ip=None):
		if "passcode" not in auth_options:
			self._set_connect_result("auth option")
		elif self.password is None:
			self._set_connect_result("no password")
		else:
			success, reason = await self.room.auth("passcode", passcode=self.password)
			if not success:
				self._set_connect_result("wrong password")
	
	async def on_disconnect(self, reason):
		pass
	
	async def on_hello(self, user_id, session, room_is_private, version, account=None,
	                   account_has_access=None, account_email_verified=None):
		pass
	
	async def on_join(self, session):
		pass
	
	async def on_login(self, account_id):
		pass
	
	async def on_logout(self):
		pass
	
	async def on_network(self, ntype, server_id, server_era):
		pass
	
	async def on_nick(self, session_id, user_id, from_nick, to_nick):
		pass
	
	async def on_edit_message(self, edit_id, message):
		pass
	
	async def on_part(self, session):
		pass
	
	async def on_ping(self, ptime, pnext):
		"""
		Default implementation, refer to api.euphoria.io
		"""
		
		logger.debug(f"&{self.room.roomname}: Pong!")
		await self.room.ping_reply(ptime)
	
	async def on_pm_initiate(self, from_id, from_nick, from_room, pm_id):
		pass
	
	async def on_send(self, message):
		pass
	
	async def on_snapshot(self, user_id, session_id, version, listing, log, nick=None,
	                      pm_with_nick=None, pm_with_user_id=None):
		if nick != self.nick:
			await self.room.nick(self.nick)
