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
	
	def add_from_data(self, data):
		"""
		add_raw(data) -> None
		
		Create a session from "raw" data and add it.
		"""
		
		ses = session.Session.from_data(data)
		
		self.sessions[ses.session_id] = ses
	
	def add(self, ses):
		"""
		add(session) -> None
		
		Add a session.
		"""
		
		self.sessions[ses.session_id] = ses
	
	def get(self, sid):
		"""
		get(session_id) -> session
		
		Returns the session with that id.
		"""
		
		return self.sessions[sid]
	
	def remove(self, ses):
		"""
		remove(session) -> None
		
		Remove a session.
		"""
		
		if ses.session_id in self.sessions:
			self.sessions.pop(ses.session_id)
	
	def remove_on_network_partition(self, server_id, server_era):
		"""
		remove_on_network_partition(server_id, server_era) -> None
		
		Removes all sessions matching the server_id/server_era combo.
		http://api.euphoria.io/#network-event
		"""
		
		# Another possible solution would be to create a new dict containing only the sessions left,
		# and then to replace the old one with the new one.
		for sid in self.sessions.keys():
			ses = self.get(sid)
			if ses.server_id == server_id and ses.server_era == server_era:
				self.remove(ses)
	
	def get_people(self):
		"""
		get_people() -> list
		
		Returns a list of all non-bot and non-lurker sessions.
		"""
		
		# not a list comprehension because that would span several lines too
		people = []
		for sid in self.sessions:
			ses = self.get(sid)
			if ses.session_type in ["agent", "account"] and ses.name:
				people.append(ses)
		return people
	
	def get_by_type(self, tp):
		"""
		get_by_type(session_type) -> list
		
		Returns a list of all non-lurker sessions with that type.
		"""
		
		return [ses for sid, ses in enumerate(self.sessions)
		        if ses.session_type == tp and ses.name]
	
	def get_accounts(self):
		"""
		get_accounts() -> list
		
		Returns a list of all logged-in sessions.
		"""
		
		return self.get_by_type("account")
	
	def get_agents(self):
		"""
		get_agents() -> list
		
		Returns a list of all sessions who are not signed into an account and not bots or lurkers.
		"""
		
		return self.get_by_type("agent")
	
	def get_bots(self):
		"""
		get_bots() -> list
		
		Returns a list of all bot sessions.
		"""
		
		return self.get_by_type("bot")
	
	def get_lurkers(self):
		"""
		get_lurkers() -> list
		
		Returns a list of all lurker sessions.
		"""
		
		return [ses for sid, ses in enumerate(self.sessions) if not ses.name]
