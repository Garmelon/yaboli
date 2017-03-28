import time

class SessionView():
	"""
	This class keeps track of session details.
	http://api.euphoria.io/#sessionview
	"""
	
	def __init__(self, id, name, server_id, server_era, session_id, is_staff=None, is_manager=None):
		"""
		id         - agent/account id
		name       - name of the client when the SessionView was captured
		server_id  - id of the server
		server_era - era of the server
		session_id - session id (unique across euphoria)
		is_staff   - client is staff
		is_manager - client is manager
		"""
		
		self.id = id
		self.name = name
		self.server_id = server_id
		self.server_era = server_era
		self.session_id = session_id
		self.staff = is_staff
		self.manager = is_manager
	
	@classmethod
	def from_data(self, data):
		"""
		Creates and returns a session created from the data.
		
		data - a euphoria SessionView
		"""
		
		return self(
			data.get("id"),
			data.get("name"),
			data.get("server_id"),
			data.get("server_era"),
			data.get("session_id"),
			data.get("is_staff"),
			data.get("is_manager")
		)
	
	def session_type(self):
		"""
		session_type() -> str
		
		The session's type (bot, account, agent).
		"""
		
		return self.id.split(":")[0] if ":" in self.id else None

class Message():
	"""
	This class represents a single euphoria message.
	http://api.euphoria.io/#message
	"""
	
	def __init__(self, id, time, sender, content, parent=None, edited=None, previous_edit_id=None,
	             deleted=None, truncated=None, encryption_key_id=None):
		"""
		id                 - message id
		time               - time the message was sent (epoch)
		sender             - SessionView of the sender
		content            - content of the message
		parent             - id of the parent message, or None
		edited             - time of last edit (epoch)
		previous_edit_id   - edit id of the most recent edit of this message
		deleted            - time of deletion (epoch)
		truncated          - message was truncated
		encryption_key_id  - id of the key that encrypts the message in storage
		"""
		
		self.id = id
		self.time = time
		self.sender = sender
		self.content = content
		self.parent = parent
		self.edited = edited
		self.previous_edit_id = previous_edit_id
		self.deleted = deleted
		self.truncated = truncated
		self.encryption_key_id = encryption_key_id
	
	@classmethod
	def from_data(self, data):
		"""
		Creates and returns a message created from the data.
		NOTE: This also creates a session object using the data in "sender".
		
		data - a euphoria message: http://api.euphoria.io/#message
		"""
		
		sender = SessionView.from_data(data.get("sender"))
		
		return self(
			data.get("id"),
			data.get("time"),
			sender,
			data.get("content"),
			parent=data.get("parent"),
			edited=data.get("edited"),
			deleted=data.get("deleted"),
			truncated=data.get("truncated"),
			previous_edit_id=data.get("previous_edit_id"),
			encryption_key_id=data.get("encryption_key_id")
		)
	
	def time_formatted(self, date=True):
		"""
		time_formatted(date=True) -> str
		
		date - include date in format
		
		Time in a readable format:
		With date:    YYYY-MM-DD HH:MM:SS
		Without date: HH:MM:SS
		"""
		
		if date:
			return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.time))
		else:
			return time.strftime("%H:%M:%S", time.gmtime(self.time))
	
	def formatted(self, show_time=False, date=True, insert_string=None, repeat_insert_string=True):
		"""
		formatted() -> strftime
		
		The message contents in the following format (does not end on a newline):
		<time><insert_string>[<sender name>] message content
		      <insert_string>                more message on a new line
		
		If repeat_insert_string is False, the insert_string will only appear
		on the first line.
		
		If show_time is False, the time will not appear in the first line of
		the formatted message.
		The date option works like it does in Message.time_formatted().
		"""
		
		msgtime = self.time_formatted(date) if show_time else ""
		if insert_string is None:
			insert_string = " " if show_time else ""
		lines = self.content.split("\n")
		
		# first line
		msg = "{}{}[{}] {}\n".format(msgtime, insert_string, self.sender.name, lines[0])
		
		# all other lines
		for line in lines[1:]:
			msg += "{}{} {}  {}\n".format(
				" "*len(msgtime),
				insert_string if repeat_insert_string else " "*len(insert_string),
				" "*len(self.sender.name),
				line
			)
		
		return msg[:-1] # remove trailing newline
