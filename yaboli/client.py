from typing import List, Optional

from .room import Room

__all__ = ["Client"]

class Client:

    # Joining and leaving rooms

    async def join(self,
            room_name: str,
            password: Optional[str] = None,
            nick: str = "") -> Room:
        pass

    async def get(self, room_name: str) -> Optional[Room]:
        pass

    async def get_all(self, room_name: str) -> List[Room]:
        pass
