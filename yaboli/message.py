import datetime
from typing import TYPE_CHECKING, Any, Optional

from .session import LiveSession, Session

if TYPE_CHECKING:
    from .room import Room

__all__ = ["Message", "LiveMessage"]

class Message:
    pass
#    @property
#    def room_name(self) -> str:
#        return self._room_name
#
#    @property
#    def time(self) -> datetime.datetime:
#        return datetime.datetime.fromtimestamp(self.timestamp)
#
#    @property
#    def timestamp(self) -> int:
#        return self._timestamp

class LiveMessage(Message):
    pass

    @classmethod
    def from_data(cls, room: "Room", data: Any) -> "LiveMessage":
        pass
