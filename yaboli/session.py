import logging

from .callbacks import Callbacks
from .connection import Connection
from .basic_types import Message, SessionView

logger = logging.getLogger(__name__)

class Session():
	"""
	Deals with the things arising from being connected to a room, such as:
	 - playing ping pong
	 - having a name (usually)
	 - seeing other clients
	 - sending and receiving messages
	
	Events:
	enter  - can view the room
	ready  - can view the room and post messages (has a nick)
	
	"""
	
	def __init__(self, room, password=None, name=None):
		self._connection = Connection(room)
		self._connection.subscribe("disconnect", self._reset_variables)
		self._connection.subscribe("bounce-event", self.handle_bounce_event)
		self._connection.subscribe("disconnect-event", self.handle_disconnect_event)
		self._connection.subscribe("hello-event", self.handle_hello_event)
		self._connection.subscribe("ping-event", self.handle_ping_event)
		self._connection.subscribe("snapshot-event", self.handle_snapshot_event)
		
		self._callbacks = Callbacks()
		self.subscribe("enter", self._on_enter)
		
		self.password = password
		self._wish_name = name
		
		#self._hello_event_completed = False
		#self._snapshot_event_completed = False
		#self._ready = False
		#self.my_session = SessionView(None, None, None, None, None)
		#self.sessions = {} # sessions in the room
		#self.room_is_private = None
		#self.server_version = None
		
		self._reset_variables()
	
	def _reset_variables(self):
		logger.debug("Resetting room-related variables")
		self.my_session = SessionView(None, None, None, None, None)
		self.sessions = {}
		self._hello_event_completed = False
		self._snapshot_event_completed = False
		self._ready = False
		
		self.room_is_private = None
		self.server_version = None
	
	def _set_name(self, new_name):
		with self._connection as conn:
			logger.debug("setting name to {!r}".format(new_name))
			conn.subscribe_to_next(self.handle_nick_reply)
			conn.send_packet("nick", name=new_name)
	
	def _on_enter(self):
		logger.info("Connected and authenticated.")
		
		if self._wish_name:
			self._set_name(self._wish_name)
	
	def launch(self):
		return self._connection.launch()
	
	def stop(self):
		logger.info("Stopping")
		with self._connection as conn:
			conn.stop()
	
	def subscribe(self, event, callback, *args, **kwargs):
		logger.debug("Adding callback {} to {}".format(callback, event))
		self._callbacks.add(event, callback, *args, **kwargs)
	
	@property
	def name(self):
		return self.my_session.name
	
	@name.setter
	def name(self, new_name):
		self._wish_name = new_name
		
		if not self._ready:
			self._set_name(new_name)
	
	def handle_bounce_event(self, data, packet):
		if data.get("reason") == "authentication required":
			if self.password:
				with self._connection as conn:
					conn.subscribe_to_next(self.handle_auth_reply)
					conn.send_packet("auth", type="passcode", passcode=self.password)
			else:
				logger.warn("Could not access &{}: No password.".format(self._connection.room))
				self.stop()
	
	def handle_disconnect_event(self, data, packet):
		self._connection.disconnect() # should reconnect
	
	def handle_hello_event(self, data, packet):
		self.my_session.read_data(data.get("session"))
		
		self.room_is_private = data.get("room_is_private")
		self.server_version = data.get("version")
		
		self._hello_event_completed = True
		if self._snapshot_event_completed:
			self._callbacks.call("enter")
	
	def handle_ping_event(self, data, packet):
		with self._connection as conn:
			logger.debug("playing ping pong")
			conn.send_packet("ping-reply", time=data.get("time"))
	
	def handle_snapshot_event(self, data, packet):
		# deal with connected sessions
		for item in data.get("listing"):
			view = SessionView.from_data(item)
			self.sessions[view.session_id] = view
		
		# deal with messages
		# TODO: this
		
		# deal with other info
		self.server_version = data.get("version")
		if "nick" in data:
			self.my_session.name = data.get("nick")
		
		self._snapshot_event_completed = True
		if self._hello_event_completed:
			self._callbacks.call("enter")
		
	
	def handle_auth_reply(self, data, packet):
		if not data.get("success"):
			logger.warn("Could not authenticate, reason: {!r}".format(data.get("reason")))
			self.stop()
		else:
			logger.debug("Authetication complete, password was correct.")
	
	def handle_nick_reply(self, data, packet):
		first_name = not self.name
		
		if first_name:
			logger.info("Changed name to {!r}.".format(data.get("to")))
		else:
			logger.info("Changed name from {!r} to {!r}.".format(data.get("from"), data.get("to")))
		
		self.my_session.name = data.get("to")
		
		if first_name:
			self._ready = True
			self._callbacks.call("ready")
