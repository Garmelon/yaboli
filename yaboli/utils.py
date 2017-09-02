__all__ = [
	"mention", "mention_reduced", "similar",
	"Session", "Listing",
	"Message", "Log",
	"ResponseError"
]



def mention(nick):
	return "".join(c for c in nick if c not in ".!?;&<'\"" and not c.isspace())

def mention_reduced(nick):
	return mention(nick).lower()

def similar(nick1, nick2):
	return mention_reduced(nick1) == mention_reduced(nick2)

class Session:
	def __init__(self, user_id, nick, server_id, server_era, session_id, is_staff=None,
	             is_manager=None, client_address=None, real_address=None):
		self.user_id = user_id
		self.nick = nick
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
			d.get("is_staff", None),
			d.get("is_manager", None),
			d.get("client_address", None),
			d.get("real_address", None)
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
	
	def remove_combo(self, server_id, server_era):
		self._sessions = {i: ses for i, ses in self._sessions.items
		                  if ses.server_id != server_id and ses.server_era != server_era}
	
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
			d.get("parent", None),
			d.get("previous_edit_id", None),
			d.get("encryption_key", None),
			d.get("edited", None),
			d.get("deleted", None),
			d.get("truncated", None)
		)

class Log:
	pass # TODO

class ResponseError(Exception):
	pass
