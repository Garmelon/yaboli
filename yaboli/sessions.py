from . import session

class Sessions():
	"""
	Keeps track of sessions.
	"""
	
	def __init__(self):
		"""
		TODO
		"""
		self._sessions = {}
	
	def add_from_data(self, data):
		"""
		add_raw(data) -> None
		
		Create a session from "raw" data and add it.
		"""
		
		ses = session.Session.from_data(data)
		
		self._sessions[ses.session_id] = ses
	
	def add(self, ses):
		"""
		add(session) -> None
		
		Add a session.
		"""
		
		self._sessions[ses.session_id] = ses
	
	def get(self, sid):
		"""
		get(session_id) -> Session
		
		Returns the session with that id.
		"""
		
		if sid in self._sessions:
			return self._sessions[sid]
	
	def remove(self, sid):
		"""
		remove(session) -> None
		
		Remove a session.
		"""
		
		if sid in self._sessions:
			self._sessions.pop(sid)
	
	def remove_on_network_partition(self, server_id, server_era):
		"""
		remove_on_network_partition(server_id, server_era) -> None
		
		Removes all sessions matching the server_id/server_era combo.
		http://api.euphoria.io/#network-event
		"""
		
		sesnew = {}
		for sid in self._sessions:
			ses = self.get(sid)
			if not (ses.server_id == server_id and ses.server_era == server_era):
				sesnew[sid] = ses
		self._sessions = sesnew
	
	def remove_all(self):
		"""
		remove_all() -> None
		
		Removes all sessions.
		"""
		
		self._sessions = {}
	
	def get_all(self):
		"""
		get_all() -> list
		
		Returns the full list of sessions.
		"""
		
		return [ses for sid, ses in self._sessions.items()]
	
	def get_people(self):
		"""
		get_people() -> list
		
		Returns a list of all non-bot and non-lurker sessions.
		"""
		
		# not a list comprehension because that would span several lines too
		people = []
		for sid in self._sessions:
			ses = self.get(sid)
			if ses.session_type() in ["agent", "account"] and ses.name:
				people.append(ses)
		return people
	
	def _get_by_type(self, tp):
		"""
		_get_by_type(session_type) -> list
		
		Returns a list of all non-lurker sessions with that type.
		"""
		
		return [ses for sid, ses in self._sessions.items()
		        if ses.session_type() == tp and ses.name]
	
	def get_accounts(self):
		"""
		get_accounts() -> list
		
		Returns a list of all logged-in sessions.
		"""
		
		return self._get_by_type("account")
	
	def get_agents(self):
		"""
		get_agents() -> list
		
		Returns a list of all sessions who are not signed into an account and not bots or lurkers.
		"""
		
		return self._get_by_type("agent")
	
	def get_bots(self):
		"""
		get_bots() -> list
		
		Returns a list of all bot sessions.
		"""
		
		return self._get_by_type("bot")
	
	def get_lurkers(self):
		"""
		get_lurkers() -> list
		
		Returns a list of all lurker sessions.
		"""
		
		return [ses for sid, ses in self._sessions.items() if not ses.name]
