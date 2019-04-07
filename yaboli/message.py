import datetime
from typing import TYPE_CHECKING, Optional

from .user import LiveUser, User

if TYPE_CHECKING:
    from .client import Client
    from .room import Room

__all__ = ["Message", "LiveMessage"]

# "Offline" message
class Message:
    def __init__(self,
            room_name: str,
            id_: str,
            parent_id: Optional[str],
            timestamp: int,
            sender: User,
            content: str,
            deleted: bool,
            truncated: bool):
        self._room_name = room_name
        self._id = id_
        self._parent_id = parent_id
        self._timestamp = timestamp
        self._sender = sender
        self._content = content
        self._deleted = deleted
        self._truncated = truncated

    @property
    def room_name(self) -> str:
        return self._room_name

    @property
    def id(self) -> str:
        return self._id

    @property
    def parent_id(self) -> Optional[str]:
        return self._parent_id

    @property
    def time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp)

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @property
    def sender(self) -> User:
        return self._sender

    @property
    def content(self) -> str:
        return self._content

    @property
    def deleted(self) -> bool:
        return self._deleted

    @property
    def truncated(self) -> bool:
        return self._truncated

# "Online" message
# has a few nice functions
class LiveMessage(Message):
    def __init__(self,
            client: 'Client',
            room: 'Room',
            id_: str,
            parent_id: Optional[str],
            timestamp: int,
            sender: LiveUser,
            content: str,
            deleted: bool,
            truncated: bool):
        self._client = client
        super().__init__(room.name, id_, parent_id, timestamp, sender, content,
                deleted, truncated)
        self._room = room
        # The typechecker can't use self._sender directly, because it has type
        # User.
        #
        # TODO Find a way to satisfy the type checker without having this
        # duplicate around, if possible?
        self._livesender = sender

    @property
    def room(self) -> 'Room':
        return self._room

    @property
    def sender(self) -> LiveUser:
        return self._livesender

    async def reply(self, text: str) -> None:
        pass

    # TODO add some sort of permission guard that checks the room
    # UnauthorizedException
    async def delete(self,
            deleted: bool = True
            ) -> None:
        pass
