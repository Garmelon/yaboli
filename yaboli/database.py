import asyncio
from functools import wraps
import sqlite3
import threading

__all__ = ["Database"]



def shielded(afunc):
	#@wraps(afunc)
	async def wrapper(*args, **kwargs):
		return await asyncio.shield(afunc(*args, **kwargs))
	return wrapper

class PooledConnection:
	def __init__(self, pool):
		self._pool = pool
		
		self.connection = None
	
	async def open(self):
		self.connection = await self._pool._request()
		print(self.connection)
	
	async def close(self):
		conn = self.connection
		self.connection = None
		await self._pool._return(conn)
	
	async def __aenter__(self):
		await self.open()
		return self
	
	async def __aexit__(self, exc_type, exc, tb):
		await self.close()

class Pool:
	def __init__(self, filename, size=10):
		self.filename = filename
		self.size = size
		
		self._available_connections = asyncio.Queue()
		
		for i in range(size):
			conn = sqlite3.connect(self.filename, check_same_thread=False)
			self._available_connections.put_nowait(conn)
	
	def connection(self):
		return PooledConnection(self)
	
	async def _request(self):
		return await self._available_connections.get()
	
	async def _return(self, conn):
		await self._available_connections.put(conn)

class Database:
	def __init__(self, filename, pool_size=10, event_loop=None):
		self._filename = filename
		self._pool = Pool(filename, size=pool_size)
		self._loop = event_loop or asyncio.get_event_loop()
	
	def operation(func):
		@wraps(func)
		@shielded
		async def wrapper(self, *args, **kwargs):
			async with self._pool.connection() as conn:
				return await self._run_in_thread(func, conn.connection, *args, **kwargs)
		return wrapper
	
	@staticmethod
	def _target_function(loop, future, func, *args, **kwargs):
		result = None
		try:
			result = func(*args, **kwargs)
		finally:
			loop.call_soon_threadsafe(future.set_result, result)
	
	async def _run_in_thread(self, func, *args, **kwargs):
		finished = asyncio.Future()
		target_args = (self._loop, finished, func, *args)
		
		thread = threading.Thread(target=self._target_function, args=target_args, kwargs=kwargs)
		thread.start()
		
		await finished
		return finished.result()
