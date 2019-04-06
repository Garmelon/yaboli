from .message import Message
from .room import Room
from .user import User

from typing import List, Optional

__all__ = ["Client"]

class Client:

    # Joining and leaving rooms

    async def join(self,
            room_name: str,
            password: str = None,
            nick: str = None) -> Room:
        pass

    async def get(self, room_name: str) -> Optional[Room]:
        pass

    async def get_all(self, room_name: str) -> List[Room]:
        pass
