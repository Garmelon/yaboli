import asyncio
import logging
import sqlite3
from typing import Any, Awaitable, Callable, TypeVar

from .util import asyncify

logger = logging.getLogger(__name__)

__all__ = ["Database", "operation"]

T = TypeVar('T')

def operation(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
        async with self as db:
            while True:
                try:
                    return await asyncify(func, self, db, *args, **kwargs)
                except sqlite3.OperationalError as e:
                    logger.warn(f"Operational error encountered: {e}")
                    await asyncio.sleep(5)
    return wrapper

class Database:
    def __init__(self, database: str) -> None:
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._lock = asyncio.Lock()

        self.initialize(self._connection)

    def initialize(self, db: Any) -> None:
        pass

    async def __aenter__(self) -> Any:
        await self._lock.__aenter__()
        return self._connection

    async def __aexit__(self, *args: Any, **kwargs: Any) -> Any:
        return await self._lock.__aexit__(*args, **kwargs)
