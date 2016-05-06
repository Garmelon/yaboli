class Session():
	"""
	This class keeps track of session details.
	"""
	
	def __init__(self, session):
		"""
		session - a euphoria SessionView: http://api.euphoria.io/#sessionview
		"""
		
		self.session = session
	
	def session_type(self):
		"""
		session_type() -> str
		
		The session's type (bot, account, agent).
		"""
		
		return self.user_id().split(":")[0]
	
	def user_id(self):
		"""
		user_id() -> str
		
		The user's id.
		"""
		
		return self.session["id"]
	
	def session_id(self):
		"""
		session_id() -> str
		
		Returns the session's id.
		"""
		
		return self.session["session_id"]
	
	def name(self):
		"""
		name() -> str
		
		The user's name.
		"""
		
		return self.session["name"]
	
	def mentionable(self):
		"""
		mentionable() -> str
		
		Converts the name to a mentionable format.
		"""
		
		return "".join(c for c in self.name() if not c in ",.!?;&<'\"" and not c.isspace())
	
	def listable(self, width):
		"""
		listable(width): -> prefixes, name
		
		Prefixes and name which together are <width> characters long or shorter.
		"""
		
		prefixes = ""
		if self.session_type() == "account":
			prefixes += "*"
		if self.is_manager():
			prefixes += "m"
		if self.is_staff():
			prefixes += "s"
		
		name = self.name()
		if len(prefixes + name) > width:
			name = name[:width - len(prefixes) - 1] + "…"
		
		return prefixes, name
	
	def server_id(self):
		"""
		server_id() -> server_id
		
		The session's server id.
		"""
		
		return self.session["server_id"]
	
	def server_era(self):
		"""
		server_era() -> server_era
		
		The session's server era.
		"""
		
		return self.session["server_era"]
	
	def is_staff(self):
		"""
		is_staff() -> staff
		
		Is a user staff?
		"""
		if "is_staff" in self.session:
			return self.session["is_staff"]
		else:
			return False
	
	def is_manager(self):
		"""
		is_manager() -> manager
		
		Is a user manager?
		"""
		if "is_manager" in self.session:
			return self.session["is_manager"]
		else:
			return False
	