import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List

logger = logging.getLogger(__name__)

__all__ = ["Events"]

class Events:
    def __init__(self) -> None:
        self._callbacks: Dict[str, List[Callable[..., Awaitable[None]]]] = {}

    def register(self,
            event: str,
            callback: Callable[..., Awaitable[None]]
            ) -> None:
        callback_list = self._callbacks.get(event, [])
        callback_list.append(callback)
        self._callbacks[event] = callback_list
        logger.debug(f"Registered callback for event {event!r}")

    async def fire(self, event: str, *args: Any, **kwargs: Any) -> None:
        logger.debug(f"Calling callbacks for event {event!r}")
        for callback in self._callbacks.get(event, []):
            asyncio.create_task(callback(*args, **kwargs))
