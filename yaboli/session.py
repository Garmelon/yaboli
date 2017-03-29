import logging

from .callbacks import Callbacks
from .connection import Connection
from .basic_types import Message, SessionView, mention

logger = logging.getLogger(__name__)

class Session():
	"""
	Deals with the things arising from being connected to a room, such as:
	 - playing ping pong
	 - having a name (usually)
	 - seeing other clients
	 - sending and receiving messages
	
	event (args)       | meaning
	-------------------|-------------------------------------------------
	enter              | can view the room
	ready              | can view the room and post messages (has a nick)
	sessions-update    | self.sessions has changed
	own-session-update | your own message has changed
	message (msg)      | a message has been received (no own messages)
	own-message (msg)  | a message that you have sent
	
	"""
	
	def __init__(self, room, password=None, name=None):
		self._connection = Connection(room)
		self._connection.subscribe("disconnect", self._reset_variables)
		
		self._connection.subscribe("bounce-event", self.handle_bounce_event)
		self._connection.subscribe("disconnect-event", self.handle_disconnect_event)
		self._connection.subscribe("hello-event", self.handle_hello_event)
		self._connection.subscribe("join-event", self.handle_join_event)
		self._connection.subscribe("logout-event", self.handle_logout_event)
		self._connection.subscribe("network-event", self.handle_network_event)
		self._connection.subscribe("nick-event", self.handle_nick_event)
		self._connection.subscribe("edit-message-event", self.handle_edit_message_event)
		self._connection.subscribe("part-event", self.handle_part_event)
		self._connection.subscribe("ping-event", self.handle_ping_event)
		self._connection.subscribe("pm-initiate-event", self.handle_pm_initiate_event)
		self._connection.subscribe("send-event", self.handle_send_event)
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
			logger.debug("Setting name to {!r}".format(new_name))
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
	
	def send(self, content, parent=None):
		if self._ready:
			self._connection.send_packet("send", content=content, parent=parent)
			logger.debug("Message sent.")
		else:
			logger.warn("Attempted to send message while not ready.")
	
	@property
	def name(self):
		return self.my_session.name
	
	@name.setter
	def name(self, new_name):
		self._wish_name = new_name
		
		if not self._ready:
			self._set_name(new_name)
	
	def refresh_sessions(self):
		logger.debug("Refreshing sessions")
		self._connection.send_packet("who")
	
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
		self._callbacks.call("own-session-update")
		
		self.room_is_private = data.get("room_is_private")
		self.server_version = data.get("version")
		
		self._hello_event_completed = True
		if self._snapshot_event_completed:
			self._callbacks.call("enter")
	
	def handle_join_event(self, data, packet):
		view = SessionView.from_data(data)
		self.sessions[view.session_id] = view
		
		if view.name:
			logger.debug("@{} joined the room.".format(mention(view.name)))
		else:
			logger.debug("Someone joined the room.")
		
		self._callbacks.call("sessions-update")
	
	def handle_logout_event(self, data, packet):
		# no idea why this should happen to the bot
		# just reconnect, in case it does happen
		self._connection.disconnect()
	
	def handle_network_event(self, data, packet):
		if data.get("type") == "partition":
			prev_len = len(self.sessions)
			
			# only remove views matching the server_id/server_era combo
			self.sessions = {
				sid: view for sid, view in self.sessions.items()
				if view.server_id != data.get("server_id")
				or view.server_era != data.get("server_era")
			}
			
			if len(sessions) != prev_len:
				logger.info("Some people left after a network event.")
			else:
				logger.info("No people left after a network event.")
			
			self._callbacks.call("sessions-update")
	
	def handle_nick_event(self, data, packet):
		session_id = data.get("session_id")
		
		if session_id not in self.sessions:
			logger.warn("SessionView not found: Refreshing sessions.")
			self.refresh_sessions()
		else:
			self.sessions[session_id].name = data.get("to")
			
			if data.get("from"):
				logger.debug("@{} changed their name to @{}.".format(
					mention(data.get("from")),
					mention(data.get("to"))
				))
			else:
				logger.debug("Someone changed their name to @{}.".format(
					mention(data.get("to"))
				))
			
			self._callbacks.call("sessions-update")
	
	def handle_edit_message_event(self, data, packet):
		# TODO: implement
		pass
	
	def handle_part_event(self, data, packet):
		view = SessionView.from_data(data)
		if view.session_id not in self.sessions:
			logger.warn("SessionView not found: Refreshing sessions.")
			self.refresh_sessions()
		else:
			del self.sessions[view.session_id]
			
			if view.name:
				logger.debug("@{} left the room.".format(mention(view.name)))
			else:
				logger.debug("Someone left the room.")
			
			self._callbacks.call("sessions-update")
	
	def handle_ping_event(self, data, packet):
		with self._connection as conn:
			conn.send_packet("ping-reply", time=data.get("time"))
	
	def handle_pm_initiate_event(self, data, error):
		pass # placeholder, maybe implemented in the future
	
	def handle_send_event(self, data, error):
		# TODO: implement
		msg = Message.from_data(data)
		self._callbacks.call("message", msg)
	
	def handle_snapshot_event(self, data, packet):
		# deal with connected sessions
		for item in data.get("listing"):
			view = SessionView.from_data(item)
			self.sessions[view.session_id] = view
		self._callbacks.call("sessions-update")
		
		# deal with messages
		# TODO: implement
		
		# deal with other info
		self.server_version = data.get("version")
		if "nick" in data:
			self.my_session.name = data.get("nick")
			self._callbacks.call("own-session-update")
		
		self._snapshot_event_completed = True
		if self._hello_event_completed:
			self._callbacks.call("enter")
		
	
	def handle_auth_reply(self, data, packet):
		if not data.get("success"):
			logger.warn("Could not authenticate, reason: {!r}".format(data.get("reason")))
			self.stop()
		else:
			logger.debug("Authetication complete, password was correct.")
	
	def handle_get_message_reply(self, data, packet):
		# TODO: implement
		pass
	
	def handle_log_event(self, data, packet):
		# TODO: implement
		pass
	
	def handle_nick_reply(self, data, packet):
		first_name = not self.name
		
		if data.get("from"):
			logger.info("Changed name from {!r} to {!r}.".format(data.get("from"), data.get("to")))
		else:
			logger.info("Changed name to {!r}.".format(data.get("to")))
		
		self.my_session.name = data.get("to")
		self._callbacks.call("own-session-update")
		
		if first_name:
			self._ready = True
			self._callbacks.call("ready")
	
	def handle_send_reply(self, data, packet):
		# TODO: implement
		msg = Message.from_data(data)
		self._callbacks.call("own-message", msg)
	
	def handle_who_reply(self, data, packet):
		for item in data.get("listing"):
			view = SessionView.from_data(item)
			self.sessions[view.session_id] = view
		self._callbacks.call("sessions-update")
