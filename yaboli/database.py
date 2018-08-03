import asyncio
import logging
import sqlite3

from .utils import *


logger = logging.getLogger(__name__)
__all__ = ["Database", "operation"]


def operation(func):
	async def wrapper(self, *args, **kwargs):
		async with self as db:
			while True:
				try:
					return await asyncify(func, self, db, *args, **kwargs)
				except sqlite3.OperationalError as e:
					logger.warn(f"Operational error encountered: {e}")
					await asyncio.sleep(5)
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
