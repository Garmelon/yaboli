class Session():
	"""
	This class keeps track of session details.
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
		
		data - a euphoria SessionView: http://api.euphoria.io/#sessionview
		"""
		
		is_staff = data["is_staff"] if "is_staff" in data else None
		is_manager = data["is_manager"] if "is_manager" in data else None
		
		return self(
			data["id"],
			data["name"],
			data["server_id"],
			data["server_era"],
			data["session_id"],
			is_staff,
			is_manager
		)
	
	def session_type(self):
		"""
		session_type() -> str
		
		The session's type (bot, account, agent).
		"""
		
		return self.id.split(":")[0]
	
	def is_staff(self):
		"""
		is_staff() -> bool
		
		Is a user staff?
		"""
		
		return self.staff and True or False
	
	def is_manager(self):
		"""
		is_manager() -> bool
		
		Is a user manager?
		"""
		
		return self.staff and True or False
