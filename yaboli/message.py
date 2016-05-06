import time

from . import session

class Message():
	"""
	This class keeps track of message details.
	"""
	
	def __init__(self, message):
		"""
		message - A euphoria message: http://api.euphoria.io/#message
		"""
		
		self.message = message
		self.session = session.Session(message["sender"])
	
	def id(self):
		"""
		id() -> str
		
		The message's unique id.
		"""
		
		return self.message["id"]
	
	def parent(self):
		"""
		parent() -> str
		
		The message's parent's unique id.
		"""
		
		if "parent" in self.message:
			return self.message["parent"]
	
	def content(self):
		"""
		content() -> str
		
		The message's content.
		"""
		
		return self.message["content"]
	
	def sender(self):
		"""
		sender() -> Session
		
		The sender of the message.
		"""
		
		return self.session
	
	def time(self):
		"""
		time() -> int
		
		Unix epoch timestamp of when the message was posted.
		"""
		
		return self.message["time"]
	
	def time_formatted(self, date=False):
		"""
		time_formatted(date=False) -> str
		
		date - include date in format
		
		Time in a readable format:
		With date:    YYYY-MM-DD HH:MM:SS
		Without date: HH:MM:SS
		"""
		
		if date:
			return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.time()))
		else:
			return time.strftime("%H:%M:%S", time.gmtime(self.time()))
	
	def deleted(self):
		"""
		deleted() -> bool
		
		Is this message deleted?
		"""
		
		return True if "deleted" in self.message and self.message["deleted"] else False
