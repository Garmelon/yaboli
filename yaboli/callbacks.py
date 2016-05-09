class Callbacks():
	"""
	Manage callbacks
	"""
	
	def __init__(self):
		self._callbacks = {}
	
	def add(self, event, callback, *args, **kwargs):
		"""
		add(event, callback, *args, **kwargs) -> None
		
		Add a function to be called on event.
		The function will be called with *args and **kwargs.
		Certain arguments might be added, depending on the event.
		"""
		
		if not event in self._callbacks:
			self._callbacks[event] = []
		
		callback_info = {
			"callback": callback,
			"args": args,
			"kwargs": kwargs
		}
		
		self._callbacks[event].append(callback_info)
	
	def remove(self, event):
		"""
		remove(event) -> None
		
		Remove all callbacks attached to that event.
		"""
		
		if event in self._callbacks:
			del self._callbacks[event]
	
	def call(self, event, *args):
		"""
		call(event) -> None
		
		Call all callbacks subscribed to the event with *args and the arguments specified when the
		callback was added.
		"""
		
		if event in self._callbacks:
			for c_info in self._callbacks[event]:
				c      = c_info["callback"]
				args   = c_info["args"] + args
				kwargs = c_info["kwargs"]
				
				c(*args, **kwargs)
