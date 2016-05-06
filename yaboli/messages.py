from . import message

class Messages():
	"""
	Message storage class which preserves thread hierarchy.
	"""
	
	def __init__(self):
		self.by_id = {}
		self.by_parent = {}
	
	def add_from_data(self, data):
		"""
		add_from_data(data) -> None
		
		Create a message from "raw" data and add it.
		"""
		
		mes = message.Message(data)
		
		self.add(mes)
	
	def add(self, mes):
		"""
		add(message) -> None
		
		Add a message to the structure.
		"""
		
		self.remove(mes.id)
		
		self.by_id[mes.id] = mes
		
		if mes.parent:
			if not mes.parent in self.by_parent:
				self.by_parent[mes.parent] = []
			self.by_parent[mes.parent].append(mes)
	
	def remove(self, mes):
		"""
		remove(message) -> None
		
		Remove a message from the structure.
		"""
		
		if mes.id in self.by_id:
			self.by_id.pop(mes.id)
		
		if mes.parent and mes in self.get_children(mes.parent):
			self.by_parent[mes.parent].remove(mes)
	
	def get(self, mid):
		"""
		get(message_id) -> Message
		
		Returns the message with the given id, if found.
		"""
		
		if mid in self.by_id:
			return self.by_id[mid]
	
	def get_parent(self, mes):
		"""
		get_parent(message) -> str
		
		Returns the message's parent.
		Returns None if no parent was found.
		"""
		
		return self.get(mes.parent)
	
	def get_children(self, mes):
		"""
		get_children(message) -> list
		
		Returns a list of children of the given message.
		"""
		
		return self.by_parent[mes.id]
