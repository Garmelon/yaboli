from . import session

class Sessions():
	"""
	Keeps track of sessions.
	"""
	
	def __init__(self):
		"""
		TODO
		"""
		self.sessions = {}
	
	def add_raw(self, raw_session):
		"""
		add_raw(raw_session) -> None
		
		Create a session from raw data and add it.
		"""
		
		ses = session.Session(raw_session)
		
		self.sessions[ses.session_id()] = ses
	
	def add(self, ses):
		"""
		add(session) -> None
		
		Add a session.
		"""
		
		self.sessions[ses.session_id()] = ses
	
	def remove(self, ses):
		"""
		remove(session_id) -> None
		
		Remove a session.
		"""
		
		if ses.session_id() in self.sessions:
			self.sessions.pop(ses.session_id())
	
	def remove_on_network_partition(self, server_id, server_era):
		"""
		remove_on_network_partition(server_id, server_era) -> None
		
		Removes all sessions matching the server_id/server_era combo.
		http://api.euphoria.io/#network-event
		"""
		
		for ses in self.sessions:
			if ses.server_id() == server_id and ses.server_era() == server_era:
				self.remove(ses)
	
	def get_people(self):
		"""
		get_people() -> list
		
		Returns a list of all non-bot and non-lurker sessions.
		"""
		
		# not a list comprehension because that would span several lines too
		people = []
		for ses in self.sessions:
			if ses.session_type() in ["agent", "account"] and ses.name():
				people.append(ses)
		return people
	
	def get_accounts(self):
		"""
		get_accounts() -> list
		
		Returns a list of all logged-in sessions.
		"""
		
		return [ses for ses in self.sessions if ses.session_type() == "account" and ses.name()]
	
	def get_agents(self):
		"""
		get_agents() -> list
		
		Returns a list of all sessions who are not signed into an account and not bots or lurkers.
		"""
		
		return [ses for ses in self.sessions if ses.session_type() == "agent" and ses.name()]
	
	def get_bots(self):
		"""
		get_bots() -> list
		
		Returns a list of all bot sessions.
		"""
		
		return [ses for ses in self.sessions if ses.session_type() == "bot" and ses.name()]
	
	def get_lurkers(self):
		"""
		get_lurkers() -> list
		
		Returns a list of all lurker sessions.
		"""
		
		return [ses for ses in self.sessions if not ses.name()]
