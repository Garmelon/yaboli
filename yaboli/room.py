import asyncio
from .connection import Connection

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
		self.sessions = None
		
		self._callbacks = {}
		self._add_callbacks()
		
		if human:
			url = HUMAN_FORMAT.format(self.roomname)
		else:
			url = ROOM_FORMAT.format(self.roomname)
		self._conn = Connection(url, self._handle_packet, self.cookie)
	
	async def run(self):
		await self._conn.run()
	
	async def stop(self):
		await self._conn.stop()
	
	# CATEGORY: SESSION COMMANDS
	
	async def auth(atype, passcode):
		pass # TODO
	
	async def ping_reply(time):
		pass # TODO
	
	# CATEGORY: CHAT ROOM COMMANDS
	
	async def get_message(message_id):
		pass # TODO
	
	async def log(n, before=None):
		pass # TODO
	
	async def nick(name):
		pass # TODO
	
	async def pm_initiate(user_id):
		pass # TODO
	
	async def send(content, parent=None):
		pass # TODO
	
	async def who()
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
		ptype = packet.get("type")
		callback = self._callbacks.get(ptype)
		if callback:
			await callback(packet)
	
	async def _handle_bounce(self, packet):
		pass # TODO
	
	async def _handle_disconnect(self, packet):
		pass # TODO
	
	async def _handle_hello(self, packet):
		pass # TODO
	
	async def _handle_join(self, packet):
		pass # TODO
	
	async def _handle_login(self, packet):
		pass # TODO
	
	async def _handle_logout(self, packet):
		pass # TODO
	
	async def _handle_network(self, packet):
		pass # TODO
	
	async def _handle_nick(self, packet):
		pass # TODO
	
	async def _handle_edit_message(self, packet):
		pass # TODO
	
	async def _handle_part(self, packet):
		pass # TODO
	
	async def _handle_ping(self, packet):
		pass # TODO
	
	async def _handle_pm_initiate(self, packet):
		pass # TODO
	
	async def _handle_send(self, packet):
		pass # TODO
	
	async def _handle_snapshot(self, packet):
		pass # TODO
