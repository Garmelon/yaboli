import asyncio
import sqlite3

from .utils import *


__all__ = ["Database", "operation"]


def operation(func):
	async def wrapper(self, *args, **kwargs):
		async with self as db:
			return await asyncify(func, db, *args, **kwargs)
	return wrapper

class Database:
	def __init__(self, database):
		self._connection = sqlite3.connect(database, check_same_thread=False)
		self._lock = asyncio.Lock()

		self.initialize(self._connection)

	def initialize(self, db):
		pass

	async def __aenter__(self, *args, **kwargs):
		await self._lock.__aenter__(*args, **kwargs)
		return self._connection

	async def __aexit__(self, *args, **kwargs):
		return await self._lock.__aexit__(*args, **kwargs)
