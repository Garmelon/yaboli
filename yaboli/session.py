import logging

from .callbacks import Callbacks
from .connection import Connection

logger = logging.getLogger(__name__)

class Session():
	"""
	Deals with the things arising from being connected to a room, such as:
	 - playing ping pong
	 - having a name (usually)
	 - seeing other clients
	 - sending and receiving messages
	
	Things to wait for before being properly connected:
	hello-event
	snapshot-event
	-> connected
	
	Things to wait for before being ready:
	hello-event
	snapshot-event
	nick-reply
	-> ready
	
	When connecting to a new room:
	_hello_event_completed = False
	_snapshot_event_completed = False
	"""
	
	def __init__(self, room, password=None):
		self._connection = Connection(room)
		self._connection.add_callback("disconnect", self._on_disconnect)
		self._connection.add_callback("bounce-event", self.handle_bounce_event)
		self._connection.add_callback("ping-event", self.handle_ping_event)
		
		self._callbacks = Callbacks()
		self._hello_event_completed = False
		self._snapshot_event_completed = False
		
		self.password = password
		
		self.my_session = None
		self.sessions = {} # sessions in the room
	
	def launch(self):
		return self._connection.launch()
	
	def stop(self):
		logger.info("Stopping")
		self._connection.stop()
	
	@property
	def name(self):
		if self.my_session:
			return self.my_session.name
	
	@name.setter
	def name(self, new_name):
		with self._connection as conn:
			logger.debug("setting name to {!r}".format(new_name))
			conn.add_next_callback(self.handle_nick_reply)
			conn.send_packet("nick", name=new_name)
	
	def _on_disconnect(self):
		logger.debug("Disconnected. Resetting related variables")
		self.my_session = None
		self.sessions = {}
		self._hello_event_completed = False
		self._snapshot_event_completed = False
	
	def handle_bounce_event(self, data, error):
		if data.get("reason") == "authentication required":
			if self.password:
				with self._connection as conn:
					conn.add_next_callback(self.handle_auth_reply)
					conn.send_packet("auth", type="passcode", passcode=self.password)
			else:
				logger.warn("Could not access &{}: No password.".format(self._connection.room))
				self.stop()
	
	def handle_disconnect_event(self, data, error):
		self._connection.disconnect() # should reconnect
	
	def handle_ping_event(self, data, error):
		with self._connection as conn:
			logger.debug("playing ping pong")
			conn.send_packet("ping-reply", time=data.get("time"))
	
	def handle_auth_reply(self, data, error):
		if data.get("success"):
			logger.debug("Authetication complete, password was correct.")
		else:
			logger.warn("Could not authenticate, reason: {!r}".format(data.get("reason")))
			self.stop()
	
	def handle_nick_reply(self, data, error):
		if error:
			logger.error("nick-reply error: {!r}".format(error))
			return
		
		first_name = not self.name
		
		logger.info("Changed name fro {!r} to {!r}.".format(data.get("from"), data.get("to")))
		self.my_session.name = data.get("to")
		
		if first_name:
			self._callbacks.call("ready")
