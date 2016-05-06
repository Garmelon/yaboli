import time

from . import session

class Message():
	"""
	This class keeps track of message details.
	"""
	
	def __init__(self, id, time, sender, content, parent=None, edited=None, deleted=None,
	             truncated=None):
		"""
		id        - message id
		time      - time the message was sent (epoch)
		sender    - session of the sender
		content   - content of the message
		parent    - id of the parent message, or None
		edited    - time of last edit (epoch)
		deleted   - time of deletion (epoch)
		truncated - message was truncated
		"""
		
		self.id = id
		self time = time
		self.sender = sender
		self.content = content
		self.parent = parent
		self edited = edited
		self.deleted = deleted
		self.truncated = truncated
	
	@classmethod
	def from_data(self, data):
		"""
		Creates and returns a message created from the data.
		NOTE: This also creates a session object using the data in "sender".
		
		data - A euphoria message: http://api.euphoria.io/#message
		"""
		
		sender = session.Session.from_data(data["sender"])
		parent = data["parent"] if "parent" in data else None
		edited = data["edited"] if "edited" in data else None
		deleted = data["deleted"] if "deleted" in data else None
		truncated = data["truncated"] if "truncated" in data else None
		
		return Message(
			data["id"],
			data["time"],
			sender,
			data["content"],
			parent=parent,
			edited=edited,
			deleted=deleted,
			truncated=truncated
		)
	
	def time_formatted(self, date=False):
		"""
		time_formatted(date=False) -> str
		
		date - include date in format
		
		Time in a readable format:
		With date:    YYYY-MM-DD HH:MM:SS
		Without date: HH:MM:SS
		"""
		
		if date:
			return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.time))
		else:
			return time.strftime("%H:%M:%S", time.gmtime(self.time))
	
	def is_edited(self):
		"""
		is_edited() -> bool
		
		Has this message been edited?
		"""
		
		return True if self.edited is not None else False
	
	def is_deleted(self):
		"""
		is_deleted() -> bool
		
		Has this message been deleted?
		"""
		
		return True self.deleted is not None else False
	
	def is_truncated(self):
		"""
		is_truncated() -> bool
		
		Has this message been truncated?
		"""
		
		return True self.truncated is not None else False
