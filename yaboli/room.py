import time

from . import connection
from . import message
from . import messages
from . import session
from . import sessions
from . import callbacks

class Room():
	"""
	Connects to and provides more abstract access to a room on euphoria.
	
	callback (values passed)     - description
	----------------------------------------------------------------------------------
	delete   (message)           - message has been deleted
	edit     (message)           - message has been edited
	identity                     - own session or nick has changed
	join     (session)           - user has joined the room
	message  (message)           - message has been sent
	messages                     - message data has changed
	nick     (session, old, new) - user has changed their nick
	part     (session)           - user has left the room
	ping                         - ping event has happened
	room                         - room info has changed
	sessions                     - session data has changed
	change                       - room has been changed
	"""
	
	def __init__(self, room=None, nick=None, password=None, message_limit=500):
		"""
		room          - name of the room to connect to
		nick          - nick to assume, None -> no nick
		password      - room password (in case the room is private)
		message_limit - maximum amount of messages that will be stored at a time
		                None - no limit
		"""
		
		self.room = room
		self.password = password
		self.room_is_private = None
		self.pm_with_nick = None
		self.pm_with_user = None
		
		self.nick = nick
		self.session = None
		self.message_limit = message_limit
		
		self.ping_last = 0
		self.ping_next = 0
		self.ping_offset = 0 # difference between server and local time
		
		self._messages = None
		self._sessions = None
		
		self._callbacks = callbacks.Callbacks()
		
		self._con = None
		
		if self.room:
			self.change(self.room, password=self.password)
	
	def launch(self):
		"""
		launch() -> Thread
		
		Open connection in a new thread (see connection.Connection.launch).
		"""
		
		return self._con.launch()
	
	def stop(self):
		"""
		stop() -> None
		
		Close connection to room.
		"""
		
		self._con.stop()
	
	def change(self, room, password=None):
		"""
		change(room) -> None
		
		Leave current room (if already connected) and join new room.
		Clears all messages and sessions.
		A call to launch() is necessary to start a new thread again.
		"""
		
		if self._con:
			self._con.stop()
		
		self.room = room
		self.password = password
		self.room_is_private = None
		self.pm_with_nick = None
		self.pm_with_user = None
		
		self.session = None
		
		self.ping_last = 0
		self.ping_next = 0
		self.ping_offset = 0 # difference between server and local time
		
		self._messages = messages.Messages(message_limit=self.message_limit)
		self._sessions = sessions.Sessions()
		
		self._con = connection.Connection(self.room)
		
		self._con.add_callback("bounce-event",       self._handle_bounce_event)
		self._con.add_callback("disconnect-event",   self._handle_disconnect_event)
		self._con.add_callback("hello-event",        self._handle_hello_event)
		self._con.add_callback("join-event",         self._handle_join_event)
		self._con.add_callback("network-event",      self._handle_network_event)
		self._con.add_callback("nick-event",         self._handle_nick_event)
		self._con.add_callback("edit-message-event", self._handle_edit_message_event)
		self._con.add_callback("part-event",         self._handle_part_event)
		self._con.add_callback("ping-event",         self._handle_ping_event)
		self._con.add_callback("send-event",         self._handle_send_event)
		self._con.add_callback("snapshot-event",     self._handle_snapshot_event)
		
		self._callbacks.call("change")
	
	def add_callback(self, event, callback, *args, **kwargs):
		"""
		add_callback(ptype, callback, *args, **kwargs) -> None
		
		Add a function to be called when a packet of type ptype is received.
		"""
		
		self._callbacks.add(event, callback, *args, **kwargs)
	
	def get_msg(self, mid):
		"""
		get_msg(message_id) -> Message
		
		Returns the message with the given id, if found.
		"""
		
		return self._messages.get(mid)
	
	def get_msg_parent(self, mid):
		"""
		get_msg_parent(message_id) -> Message
		
		Returns the message's parent, if found.
		"""
		
		return self._messages.get_parent(mid)
	
	def get_msg_children(self, mid):
		"""
		get_msg_children(message_id) -> list
		
		Returns a sorted list of children of the given message, if found.
		"""
		
		return self._messages.get_children(mid)
	
	def get_msg_top_level(self):
		"""
		get_msg_top_level() -> list
		
		Returns a sorted list of top-level messages.
		"""
		
		return self._messages.get_top_level()
	
	def get_msg_oldest(self):
		"""
		get_msg_oldest() -> Message
		
		Returns the oldest message, if found.
		"""
		
		return self._messages.get_oldest()
	
	def get_msg_youngest(self):
		"""
		get_msg_youngest() -> Message
		
		Returns the youngest message, if found.
		"""
		
		return self._messages.get_youngest()
	
	def get_session(self, sid):
		"""
		get_session(session_id) -> Session
		
		Returns the session with that id.
		"""
		
		return self._sessions.get(sid)
	
	def get_sessions(self):
		"""
		get_sessions() -> list
		
		Returns the full list of sessions.
		"""
		
		return self._sessions.get_all()
	
	def get_people(self):
		"""
		get_people() -> list
		
		Returns a list of all non-bot and non-lurker sessions.
		"""
		
		return self._sessions.get_people()
	
	def get_accounts(self):
		"""
		get_accounts() -> list
		
		Returns a list of all logged-in sessions.
		"""
		
		return self._sessions.get_accounts()
	
	def get_agents(self):
		"""
		get_agents() -> list
		
		Returns a list of all sessions who are not signed into an account and not bots or lurkers.
		"""
		
		return self._sessions.get_agents()
	
	def get_bots(self):
		"""
		get_bots() -> list
		
		Returns a list of all bot sessions.
		"""
		
		return self._sessions.get_bots()
	
	def get_lurkers(self):
		"""
		get_lurkers() -> list
		
		Returns a list of all lurker sessions.
		"""
		
		return self._sessions.get_lurkers()
	
	def set_nick(self, nick):
		"""
		set_nick(nick) -> None
		
		Change your nick.
		"""
		
		self._con.add_next_callback(self._handle_nick_reply)
		self._con.send_packet("nick", name=nick)
	
	def mentionable(self, name=None):
		"""
		mentionable()
		
		A mentionable version of the name.
		The name defaults to the bot's name.
		"""
		
		if name is None:
			name = self.nick
		
		return "".join(c for c in name if not c in ".!?;&<'\"" and not c.isspace())
	
	def send_message(self, content, parent=None):
		"""
		send_message(content, parent) -> None
		
		Send a message.
		"""
		
		self._con.add_next_callback(self._handle_send_reply)
		self._con.send_packet("send", content=content, parent=parent)
	
	def authenticate(self, password=None):
		"""
		authenticate(passsword) -> None
		
		Try to authenticate so you can enter the room.
		"""
		
		self.password = password
		
		self._con.add_next_callback(self._handle_auth_reply)
		self._con.send_packet("auth", type="passcode", passcode=self.password)
	
	def update_sessions(self):
		"""
		update_sessions() -> None
		
		Resets and then updates the list of sessions.
		"""
		
		self._con.add_next_callback(self._handle_who_reply)
		self._con.send_packet("who")
	
	def load_msgs(self, number=50):
		"""
		load_msgs(number) -> None
		
		Request a certain number of older messages from the server.
		"""
		
		self._con.add_next_callback(self._handle_log_reply)
		self._con.send_packet("log", n=number, before=self.get_msg_oldest().id)
	
	def load_msg(self, mid):
		"""
		load_msg(message_id) -> None
		
		Request an untruncated version of the message with that id.
		"""
		
		self._con.add_next_callback(self._handle_get_message_reply)
		self._con.send_packet("get-message", id=mid)
	
	# ----- HANDLING OF EVENTS -----
	
	def _handle_connect(self):
		"""
		TODO
		"""
		
		self._callbacks.call("connect")
	
	def _handle_disconnect(self):
		"""
		TODO
		"""
		
		self._callbacks.call("disconnect")
	
	def _handle_stop(self):
		"""
		TODO
		"""
		
		self._callbacks.call("stop")
	
	def _handle_bounce_event(self, data):
		"""
		TODO
		"""
		
		if self.password is not None:
			self.authenticate(self.password)
	
	def _handle_disconnect_event(self, data):
		"""
		TODO
		"""
		
		self._con.disconnect()
	
	def _handle_hello_event(self, data):
		"""
		TODO
		"""
		
		self.session = session.Session.from_data(data["session"])
		self._sessions.add(self.session)
		self._callbacks.call("identity")
		self._callbacks.call("sessions")
		
		self.room_is_private = data["room_is_private"]
		self._callbacks.call("room")
	
	def _handle_join_event(self, data):
		"""
		TODO
		"""
		
		ses = session.Session.from_data(data)
		self._sessions.add(ses)
		self._callbacks.call("join", ses)
		self._callbacks.call("sessions")
	
	def _handle_network_event(self, data):
		"""
		TODO
		"""
		
		if data["type"] == "partition":
			self._sessions.remove_on_network_partition(data["server_id"], data["server_era"])
			self._callbacks.call("sessions")
	
	def _handle_nick_event(self, data):
		"""
		TODO
		"""
		
		ses = self.get_session(data["session_id"])
		if ses:
			ses.name = data["to"]
			self._callbacks.call("nick", ses, data["from"], data["to"])
			self._callbacks.call("sessions")
	
	def _handle_edit_message_event(self, data):
		"""
		TODO
		"""
		
		msg = message.Message.from_data(data)
		if msg:
			self._messages.add(msg)
			
			if msg.deleted:
				self._callbacks.call("delete", msg)
			elif msg.edited:
				self._callbacks.call("edit", msg)
			
			self._callbacks.call("messages")
	
	def _handle_part_event(self, data):
		"""
		TODO
		"""
		
		ses = session.Session.from_data(data)
		if ses:
			self._sessions.remove(ses.session_id)
			
			self._callbacks.call("part", ses)
			self._callbacks.call("sessions")
	
	def _handle_ping_event(self, data):
		"""
		TODO
		"""
		
		self.ping_last = data["time"]
		self.ping_next = data["next"]
		self.ping_offset = self.ping_last - time.time()
		
		self._con.send_packet("ping-reply", time=self.ping_last)
		self._callbacks.call("ping")
	
	def _handle_send_event(self, data):
		"""
		TODO
		"""
		
		msg = message.Message.from_data(data)
		self._callbacks.call("message", msg)
		
		self._messages.add(msg)
		self._callbacks.call("messages")
	
	def _handle_snapshot_event(self, data):
		"""
		TODO
		"""
		
		self.set_nick(self.nick)
		
		if "pm_with_nick" in data or "pm_with_user_id" in data:
			if "pm_with_nick" in data:
				self.pm_with_nick = data["pm_with_nick"]
			if "pm_with_user_id" in data:
				self.pm_with_user_id = data["pm_with_user_id"]
			self._callbacks.call("room")
		
		self._sessions.remove_all()
		for sesdata in data["listing"]:
			self._sessions.add_from_data(sesdata)
		self._callbacks.call("sessions")
		
		self._messages.remove_all()
		for msgdata in data["log"]:
			self._messages.add_from_data(msgdata)
		self._callbacks.call("messages")
	
	# ----- HANDLING OF REPLIES -----
	
	def _handle_auth_reply(self, data):
		"""
		TODO
		"""
		
		if not data["success"]:
			self._con.stop()
	
	def _handle_get_message_reply(self, data):
		"""
		TODO
		"""
		
		self._messages.add_from_data(data)
		self._callbacks.call("messages")
	
	def _handle_log_reply(self, data):
		"""
		TODO
		"""
		
		for msgdata in data["log"]:
			self._messages.add_from_data(msgdata)
		self._callbacks.call("messages")
	
	def _handle_nick_reply(self, data):
		"""
		TODO
		"""
		
		if "to" in data:
			self.nick = data["to"]
			self.session.name = self.nick
			self._callbacks.call("identity")
	
	def _handle_send_reply(self, data):
		"""
		TODO
		"""
		
		self._messages.add_from_data(data)
		self._callbacks.call("messages")
	
	def _handle_who_reply(self, data):
		"""
		TODO
		"""
		
		self._sessions.remove_all()
		for sesdata in data["listing"]:
			self._sessions.add_from_data(sesdata)
		self._callbacks.call("sessions")
