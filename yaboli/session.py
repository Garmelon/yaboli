import logging
import threading

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
	
	event (args)        | meaning
	--------------------|-------------------------------------------------
	join (bool)         | joining the room was successful/not successful
	                    | Callbacks for this event are cleared whenever it is called.
	enter               | can view the room
	ready               | can view the room and post messages (has a nick)
	sessions-update     | self.sessions has changed
	own-session-update  | your own message has changed
	message (msg)       | a message has been received (no own messages)
	own-message (msg)   | a message that you have sent
	
	"""
	
	def __init__(self, name=None):
		self._room_accessible = False
		self._room_accessible_event = threading.Event()
		self._room_accessible_timeout = None
		
		self._connection = Connection()
		self._connection.subscribe("disconnect", self._reset_variables)
		
		self._connection.subscribe("bounce-event", self._handle_bounce_event)
		self._connection.subscribe("disconnect-event", self._handle_disconnect_event)
		self._connection.subscribe("hello-event", self._handle_hello_event)
		self._connection.subscribe("join-event", self._handle_join_event)
		self._connection.subscribe("logout-event", self._handle_logout_event)
		self._connection.subscribe("network-event", self._handle_network_event)
		self._connection.subscribe("nick-event", self._handle_nick_event)
		self._connection.subscribe("edit-message-event", self._handle_edit_message_event)
		self._connection.subscribe("part-event", self._handle_part_event)
		self._connection.subscribe("ping-event", self._handle_ping_event)
		self._connection.subscribe("pm-initiate-event", self._handle_pm_initiate_event)
		self._connection.subscribe("send-event", self._handle_send_event)
		self._connection.subscribe("snapshot-event", self._handle_snapshot_event)
		
		self._callbacks = Callbacks()
		self.subscribe("enter", self._on_enter)
		
		self.password = None
		self.real_name = name
		
		#self._hello_event_completed = False
		#self._snapshot_event_completed = False
		#self._ready = False
		#self.my_session = SessionView(None, None, None, None, None)
		#self.sessions = {} # sessions in the room
		#self.room_is_private = None
		#self.server_version = None
		
		self._reset_variables()
	
	def switch_to(self, room, password=None, timeout=10):
		logger.info("Switching to &{}.".format(room))
		self.password = password
		
		if self._room_accessible_timeout:
			self._room_accessible_timeout.cancel()
		self._room_accessible_timeout = threading.Timer(timeout, self.stop)
		self._room_accessible_timeout.start()
		
		if self._connection.connect_to(room):
			logger.debug("Connection established. Waiting for correct events")
			self._room_accessible_event.wait()
			return self._room_accessible
		else:
			logger.warn("Could not connect to room url.")
			return False
	
	def _reset_variables(self):
		logger.debug("Resetting room-related variables")
		self._room_accessible = False
		
		self.my_session = SessionView(None, None, None, None, None)
		self.sessions = {}
		self._room_accessible_event.clear()
		
		self._hello_event_completed = False
		self._snapshot_event_completed = False
		self._ready = False
		
		self.room_is_private = None
		self.server_version = None
	
	def _set_name(self, new_name):
		with self._connection as conn:
			logger.debug("Setting name to {!r}".format(new_name))
			conn.subscribe_to_next(self._handle_nick_reply)
			conn.send_packet("nick", name=new_name)
	
	def _on_enter(self):
		logger.info("Connected and authenticated.")
		self._room_accessible_timeout.cancel()
		self._room_accessible = True
		self._room_accessible_event.set()
		self._room_accessible_event.clear()
		
		if self.real_name:
			self._set_name(self.real_name)
	
	def launch(self):
		return self._connection.launch()
	
	def stop(self):
		logger.info("Stopping")
		self._room_accessible_timeout.cancel()
		self._room_accessible = False
		self._room_accessible_event.set()
		self._room_accessible_event.clear()
		
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
		self.real_name = new_name
		
		if not self._ready:
			self._set_name(new_name)
	
	@property
	def room(self):
		return self._connection.room
	
	def refresh_sessions(self):
		logger.debug("Refreshing sessions")
		self._connection.send_packet("who")
	
	def _set_sessions_from_listing(self, listing):
		self.sessions = {}
		
		for item in listing:
			view = SessionView.from_data(item)
			self.sessions[view.session_id] = view
			
		self._callbacks.call("sessions-update")
	
	def _revert_to_revious_room(self):
		self._callbacks.call("join", False)
		
		if self._prev_room:
			self.password = self._prev_password
			self.room = self._prev_room # shouldn't do this
			
			self._prev_room = None
			self._prev_password = None
		else:
			self.stop()
	
	def _handle_bounce_event(self, data, packet):
		if data.get("reason") == "authentication required":
			if self.password:
				with self._connection as conn:
					conn.subscribe_to_next(self._handle_auth_reply)
					conn.send_packet("auth", type="passcode", passcode=self.password)
			else:
				logger.warn("Could not access &{}: No password.".format(self._connection.room))
				self.stop()
	
	def _handle_disconnect_event(self, data, packet):
		self._connection.disconnect() # should reconnect
	
	def _handle_hello_event(self, data, packet):
		self.my_session.read_data(data.get("session"))
		self._callbacks.call("own-session-update")
		
		self.room_is_private = data.get("room_is_private")
		self.server_version = data.get("version")
		
		self._hello_event_completed = True
		if self._snapshot_event_completed:
			self._callbacks.call("enter")
	
	def _handle_join_event(self, data, packet):
		view = SessionView.from_data(data)
		self.sessions[view.session_id] = view
		
		if view.name:
			logger.debug("@{} joined the room.".format(mention(view.name)))
		else:
			logger.debug("Someone joined the room.")
		
		self._callbacks.call("sessions-update")
	
	def _handle_logout_event(self, data, packet):
		# no idea why this should happen to the bot
		# just reconnect, in case it does happen
		self._connection.disconnect()
	
	def _handle_network_event(self, data, packet):
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
	
	def _handle_nick_event(self, data, packet):
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
	
	def _handle_edit_message_event(self, data, packet):
		# TODO: implement
		pass
	
	def _handle_part_event(self, data, packet):
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
	
	def _handle_ping_event(self, data, packet):
		with self._connection as conn:
			conn.send_packet("ping-reply", time=data.get("time"))
	
	def _handle_pm_initiate_event(self, data, error):
		pass # placeholder, maybe implemented in the future
	
	def _handle_send_event(self, data, error):
		# TODO: implement
		msg = Message.from_data(data)
		self._callbacks.call("message", msg)
	
	def _handle_snapshot_event(self, data, packet):
		# deal with connected sessions
		self._set_sessions_from_listing(data.get("listing"))
		
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
		
	
	def _handle_auth_reply(self, data, packet):
		if not data.get("success"):
			logger.warn("Could not authenticate, reason: {!r}".format(data.get("reason")))
			self.stop()
		else:
			logger.debug("Authetication complete, password was correct.")
	
	def _handle_get_message_reply(self, data, packet):
		# TODO: implement
		pass
	
	def _handle_log_event(self, data, packet):
		# TODO: implement
		pass
	
	def _handle_nick_reply(self, data, packet):
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
	
	def _handle_send_reply(self, data, packet):
		# TODO: implement
		msg = Message.from_data(data)
		self._callbacks.call("own-message", msg)
	
	def _handle_who_reply(self, data, packet):
		self._set_sessions_from_listing(data.get("listing"))
