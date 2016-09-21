class Callbacks():
	"""
	Manage callbacks
	"""
	
	def __init__(self):
		self._callbacks = {}
	
	def add(self, event, callback):
		"""
		add(event, callback) -> None
		
		Add a function to be called on event.
		Certain arguments might be added on call, depending on the event.
		"""
		
		if not event in self._callbacks:
			self._callbacks[event] = []
		
		self._callbacks[event].append(callback)
	
	def remove(self, event):
		"""
		remove(event) -> None
		
		Remove all callbacks added to that event.
		"""
		
		if event in self._callbacks:
			del self._callbacks[event]
	
	def call(self, event, *args, **kwargs):
		"""
		call(event) -> None
		
		Call all callbacks subscribed to the event with the arguments passed to this function.
		"""
		
		if event in self._callbacks:
			for c in self._callbacks:
				c(*args, **kwargs)
	
	def exists(self, event):
		"""
		exists(event) -> bool
		
		Are any functions subscribed to this event?
		"""
		
		return event in self._callbacks
