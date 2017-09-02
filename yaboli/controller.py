from room import Room



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
	
	def __init__(self, roomname, human=False, cookie=None):
		"""
		roomname  - name of room to connect to
		human     - whether the human flag should be set on connections
		cookie    - cookie to use in HTTP request, if any
		"""
		
		self.roomname = roomname
		self.human = human
		self.cookie = cookie
		
		self.room = None
		self.running = True
	
	async def run(self):
		await self.on_start()
		
		while self.running:
			self.room = Room(self.roomname, self, self.human, self.cookie)
			await self.room.run()
			self.room = None
		
		await self.on_end()
	
	async def stop(self):
		if self.running:
			self.running = False
			
			if self.room:
				await self.room.stop()
	
	async def on_start(self):
		"""
		The first callback called when the controller is run.
		"""
		
		pass
	
	async def on_stop(self):
		"""
		The last callback called when the controller is run.
		"""
		
		pass
	
	async def on_connected(self):
		"""
		Client has successfully (re-)joined the room.
		
		Use: Actions that are meant to happen upon (re-)connecting to a room,
		     such as resetting the message history.
		"""
		
		pass
	
	async def on_disconnected(self):
		"""
		Client has disconnected from the room.
		
		This is the last time the old self.room can be accessed.
		Use: Reconfigure self before next connection.
		     Need to store information from old room?
		"""
		
		pass
	
	async def on_bounce(self, reason=None, auth_options=None, agent_id=None, ip=None):
		pass
	
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
	
	async def on_nick(self, session_id, user_id, from_name, to_name):
		pass
	
	async def on_edit_message(self, edit_id, message):
		pass
	
	async def on_part(self, session):
		pass
	
	async def on_ping(self, ptime, pnext):
		"""
		Default implementation, refer to api.euphoria.io
		"""

		await self.room.ping_reply(ptime)
	
	async def on_pm_initiate(self, from_id, from_nick, from_room, pm_id):
		pass
	
	async def on_send(self, message):
		pass
	
	async def on_snapshot(self, user_id, session_id, version, listing, log, nick=None,
	                      pm_with_nick=None, pm_with_user_id=None):
		pass
