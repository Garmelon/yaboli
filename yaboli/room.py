from . import connection
from . import messages
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
		self.nick = nick
		self.password = password
		self.account_email = account_email
		self.account_password = account_password
		
		self.messages = messages.Messages()
		self.sessions = sessions.Sessions()
		
		self.con = connection.Connection(self.room)
	
	def launch(self):
		"""
		launch() -> Thread
		
		Open connection in a new thread (see connection.Connection.launch).
		"""
		
		return self.con.launch()
