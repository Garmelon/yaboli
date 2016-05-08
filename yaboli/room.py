import time

from . import connection
from . import messages
from . import session
from . import sessions

class Room():
	"""
	Connects to and provides more abstract access to a room on euphoria.
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
		
		self.nick = nick
		self.session = None
		
		self.account_name = None
		self.account_email = account_email
		self.account_password = account_password
		
		self.ping_last = 0
		self.ping_next = 0
		self.ping_offset = 0 # difference between server and local time
		
		self.messages = messages.Messages()
		self.sessions = sessions.Sessions()
		self.callbacks = callbacks.Callbacks()
		
		self.con = connection.Connection(self.room)
		
		self.con.add_callback("hello-event", self._handle_hello_event)
		self.con.add_callback("ping-event", self._handle_ping_event)
	
	def launch(self):
		"""
		launch() -> Thread
		
		Open connection in a new thread (see connection.Connection.launch).
		"""
		
		return self.con.launch()
	
	def _handle_hello_event(self, data):
		"""
		TODO
		"""
		
		self.session = session.Session.from_data(data["session"])
		self.sessions.add(self.session)
		
		self.room_is_private = data["room_is_private"]
		
		if "account" in data: # in case you log in in another room
			self.account_name = data["account"]["name"]
			self.account_email = data["account"]["email"]
	
	def _handle_ping_event(self, data):
		"""
		TODO
		"""
		
		self.ping_last = data["time"]
		self.ping_next = data["next"]
		self.ping_offset = self.ping_last - time.gmtime()
		
		self.con.send_packet("ping-reply", time=self.ping_last)
