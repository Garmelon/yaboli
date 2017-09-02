class Session:
	def __init__(self, user_id, name, server_id, server_era, session_id, is_staff=None,
	             is_manager=None, client_address=None, real_address=None):
		self.user_id = user_id
		self.name = name
		self.server_id = server_id
		self.server_era = server_era
		self.session_id = session_id
		self.is_staff = is_staff
		self.is_manager = is_manager
		self.client_address = client_address
		self.real_address = real_address
	
	@classmethod
	def from_dict(cls, d):
		return cls(
			d.get("id"),
			d.get("name"),
			d.get("server_id"),
			d.get("server_era"),
			d.get("session_id"),
			d.get("is_staff"),
			d.get("is_manager"),
			d.get("client_address"),
			d.get("real_address")
		)
	
	@property
	def client_type(self):
		# account, agent or bot
		return self.user_id.split(":")[0]

class Listing:
	def __init__(self):
		self._sessions = {}
	
	def __len__(self):
		return len(self._sessions)
	
	def add(self, session):
		self._sessions[session.session_id] = session
	
	def remove(self, session_id):
		self._sessions.pop(session_id)
	
	def by_sid(self, session_id):
		return self._sessions.get(session_id);
	
	def by_uid(self, user_id):
		return [ses for ses in self._sessions if ses.user_id == user_id]
	
	def get_people(self):
		return {uid: ses for uid, ses in self._sessions.items()
		        if ses.client_type in ["agent", "account"]}
	
	def get_accounts(self):
		return {uid: ses for uid, ses in self._sessions.items()
		        if ses.client_type is "account"}
	
	def get_agents(self):
		return {uid: ses for uid, ses in self._sessions.items()
		        if ses.client_type is "agent"}
	
	def get_bots(self):
		return {uid: ses for uid, ses in self._sessions.items()
		        if ses.client_type is "bot"}

class Message():
	def __init__(self, message_id, time, sender, content, parent=None, previous_edit_id=None,
	             encryption_key=None, edited=None, deleted=None, truncated=None):
		self.message_id = message_id
		self.time = time
		self.sender = sender
		self.content = content
		self.parent = parent
		self.previous_edit_id = previous_edit_id
		self.encryption_key = encryption_key
		self.edited = edited
		self.deleted = deleted
		self.truncated = truncated
	
	@classmethod
	def from_dict(cls, d):
		return cls(
			d.get("id"),
			d.get("time"),
			Session.from_dict(d.get("sender")),
			d.get("content"),
			d.get("parent"),
			d.get("previous_edit_id"),
			d.get("encryption_key"),
			d.get("edited"),
			d.get("deleted"),
			d.get("truncated")
		)
