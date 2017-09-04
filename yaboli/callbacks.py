import asyncio

__all__ = ["Callbacks"]



class Callbacks():
	"""
	Manage callbacks asynchronously
	"""
	
	def __init__(self):
		self._callbacks = {}
	
	def add(self, event, callback):
		"""
		add(event, callback) -> None
		
		Add a function to be called on event.
		"""
		
		if not event in self._callbacks:
			self._callbacks[event] = []
		self._callbacks[event].append(callback)
	
	def remove(self, event):
		"""
		remove(event) -> None
		
		Remove all callbacks attached to that event.
		"""
		
		if event in self._callbacks:
			del self._callbacks[event]
	
	async def call(self, event, *args, **kwargs):
		"""
		await call(event) -> None
		
		Call all callbacks subscribed to the event with *args and **kwargs".
		"""
		
		tasks = [asyncio.ensure_future(callback(*args, **kwargs))
		         for callback in self._callbacks.get(event, [])]
		
		for task in tasks:
			await task
	
	def exists(self, event):
		"""
		exists(event) -> bool
		
		Are any functions subscribed to this event?
		"""
		
		return event in self._callbacks
