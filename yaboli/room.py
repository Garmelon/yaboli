import time

from . import connection
from . import messages
from . import session
from . import sessions
from . import callbacks

class Room():
	"""
	Connects to and provides more abstract access to a room on euphoria.
	
	Callbacks:
		- account  - account info has changed
		- identity - own session_id or identity or nick etc. has changed
		- messages - message data has changed
		- ping     - ping event has happened
		- room     - room info has changed
		- sessions - session data has changed
	"""
	
	def __init__(self, room, nick=None, password=None, account_email=None, account_password=None):
		"""
		room             - name of the room to connect to
		nick             - nick to assume, None -> no nick
		password         - room password (in case the room is private)
		account_email    - email of your account
		account_password - password of your account
		"""
		
		self.room = room
		self.room_is_private = None
		self.password = password
		self.pm_with_nick = None
		self.pm_with_user = None
		
		self.nick = nick
		self.identity = None
		self.session_id = None
		
		self.account_name = None
		self.account_email = account_email
		self.account_password = account_password
		
		self.ping_last = 0
		self.ping_next = 0
		self.ping_offset = 0 # difference between server and local time
		
		self._messages = messages.Messages()
		self._sessions = sessions.Sessions()
		self._callbacks = callbacks.Callbacks()
		
		self._con = connection.Connection(self.room)
		
		self._con.add_callback("hello-event", self._handle_hello_event)
		self._con.add_callback("ping-event", self._handle_ping_event)
		self._con.add_callback("snapshot-event", self._handle_snapshot_event)
	
	def launch(self):
		"""
		launch() -> Thread
		
		Open connection in a new thread (see connection.Connection.launch).
		"""
		
		return self._con.launch()
	
	def set_nick(self, nick):
		"""
		set_nick(nick) -> None
		
		Change your nick.
		"""
		
		self._con.add_next_callback(self._handle_nick_reply)
		self._con.send_packet("nick", name=nick)
	
	def get_msg(self, mid):
		"""
		get_msg(message_id) -> Message
		
		Returns the message with the given id, if found.
		"""
		
		return self._messages.get(mid)
	
	def get_msg_parent(self, mes):
		"""
		get_msg_parent(message) -> Message
		
		Returns the message's parent, if found.
		"""
		
		return self._messages.get_parent(mes)
	
	# ----- HANDLING OF EVENTS -----
	
	def _handle_hello_event(self, data):
		"""
		TODO
		"""
		
		ses = session.Session.from_data(data["session"])
		self._sessions.add(ses)
		self._callbacks.call("sessions")
		
		self.identity = data["id"]
		self.session_id = ses.session_id
		self._callbacks.call("identity")
		
		self.room_is_private = data["room_is_private"]
		self._callbacks.call("room")
		
		if "account" in data: # in case you log in in another room
			self.account_name = data["account"]["name"]
			self.account_email = data["account"]["email"]
			self._callbacks.call("account")
	
	def _handle_ping_event(self, data):
		"""
		TODO
		"""
		
		self.ping_last = data["time"]
		self.ping_next = data["next"]
		self.ping_offset = self.ping_last - time.time()
		
		self._con.send_packet("ping-reply", time=self.ping_last)
		self._callbacks.call("ping")
	
	def _handle_snapshot_event(self, data):
		"""
		TODO
		"""
		
		self.identity = data["identity"]
		self.session_id = data["session_id"]
		if not self.nick and "nick" in data:
			self.nick = data["nick"]
		elif self.nick:
			self.set_nick(self.nick)
		self._callbacks.call("identity")
		
		if "pm_with_nick" in data or "pm_with_user_id" in data:
			if "pm_with_nick" in data:
				self.pm_with_nick = data["pm_with_nick"]
			if "pm_with_user_id" in data:
				self.pm_with_user_id = data["pm_with_user_id"]
			self._callbacks.call("room")
		
		for sesdata in data["listing"]:
			self._sessions.add_from_data(sesdata)
		self._callbacks.call("sessions")
		
		for mesdata in data["log"]:
			self._messages.add_from_data(mesdata)
		self._callbacks.call("messages")
	
	# ----- HANDLING OF REPLIES -----
	
	def _handle_nick_reply(self, data):
		"""
		TODO
		"""
		
		self.nick = data["to"]
		
		self._callbacks.call("identity")
