import operator

from . import message

class Messages():
	"""
	Message storage class which preserves thread hierarchy.
	"""
	
	def __init__(self, message_limit=500):
		"""
		message_limit - maximum amount of messages that will be stored at a time
		                None - no limit
		"""
		
		self.message_limit = message_limit
		
		self._by_id = {}
		self._by_parent = {}
	
	def _sort(self, msgs):
		"""
		_sort(messages) -> None
		
		Sorts a list of messages by their id, in place.
		"""
		
		msgs.sort(key=operator.attrgetter("id"))
	
	def add_from_data(self, data):
		"""
		add_from_data(data) -> None
		
		Create a message from "raw" data and add it.
		"""
		
		mes = message.Message.from_data(data)
		
		self.add(mes)
	
	def add(self, mes):
		"""
		add(message) -> None
		
		Add a message to the structure.
		"""
		
		self.remove(mes.id)
		
		self._by_id[mes.id] = mes
		
		if mes.parent:
			if not mes.parent in self._by_parent:
				self._by_parent[mes.parent] = []
			self._by_parent[mes.parent].append(mes)
		
		if self.message_limit and len(self._by_id) > self.message_limit:
			self.remove(self.get_oldest().id)
	
	def remove(self, mid):
		"""
		remove(message_id) -> None
		
		Remove a message from the structure.
		"""
		
		mes = self.get(mid)
		if mes:
			if mes.id in self._by_id:
				self._by_id.pop(mes.id)
			
			parent = self.get_parent(mes.id)
			if parent and mes in self.get_children(parent.id):
				self._by_parent[mes.parent].remove(mes)
	
	def remove_all(self):
		"""
		remove_all() -> None
		
		Removes all messages.
		"""
		
		self._by_id = {}
		self._by_parent = {}
	
	def get(self, mid):
		"""
		get(message_id) -> Message
		
		Returns the message with the given id, if found.
		"""
		
		if mid in self._by_id:
			return self._by_id[mid]
	
	def get_oldest(self):
		"""
		get_oldest() -> Message
		
		Returns the oldest message, if found.
		"""
		
		oldest = None
		for mid in self._by_id:
			if oldest is None or mid < oldest:
				oldest = mid
		return self.get(oldest)
	
	def get_youngest(self):
		"""
		get_youngest() -> Message
		
		Returns the youngest message, if found.
		"""
		
		youngest = None
		for mid in self._by_id:
			if youngest is None or mid > youngest:
				youngest = mid
		return self.get(youngest)
	
	def get_parent(self, mid):
		"""
		get_parent(message_id) -> str
		
		Returns the message's parent, if found.
		"""
		
		mes = self.get(mid)
		if mes:
			return self.get(mes.parent)
	
	def get_children(self, mid):
		"""
		get_children(message_id) -> list
		
		Returns a sorted list of children of the given message, if found.
		"""
		
		if mid in self._by_parent:
			children = self._by_parent[mid][:]
			self._sort(children)
			return children
	
	def get_top_level(self):
		"""
		get_top_level() -> list
		
		Returns a sorted list of top-level messages.
		"""
		
		msgs = [self.get(mid) for mid in self._by_id if not self.get(mid).parent]
		self._sort(msgs)
		return msgs
