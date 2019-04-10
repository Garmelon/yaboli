import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from .session import LiveSession, Session

if TYPE_CHECKING:
    from .room import Room

__all__ = ["Message", "LiveMessage"]

class Message:
    def __init__(self,
            room_name: str,
            message_id: str,
            parent_id: Optional[str],
            previous_edit_id: Optional[str],
            timestamp: int,
            sender: Session,
            content: str,
            encryption_key_id: Optional[str],
            edited_timestamp: Optional[int],
            deleted_timestamp: Optional[int],
            truncated: bool
            ) -> None:
        self._room_name = room_name
        self._message_id = message_id
        self._parent_id = parent_id
        self._previous_edit_id = previous_edit_id
        self._timestamp = timestamp
        self._sender = sender
        self._content = content
        self._encryption_key_id = encryption_key_id
        self._edited_timestamp = edited_timestamp
        self._deleted_timestamp = deleted_timestamp
        self._truncated = truncated

    @classmethod
    def from_data(cls, room_name: str, data: Any) -> "Message":
        message_id = data["id"]
        parent_id = data.get("parent")
        previous_edit_id = data.get("previous_edit_id")
        timestamp = data["time"]
        sender = Session.from_data(room_name, data["sender"])
        content = data["content"]
        encryption_key_id = data.get("encryption_key_id")
        edited_timestamp = data.get("edited")
        deleted_timestamp = data.get("deleted")
        truncated = data.get("truncated", False)

        return cls(room_name, message_id, parent_id, previous_edit_id,
                timestamp, sender, content, encryption_key_id,
                edited_timestamp, deleted_timestamp, truncated)

    # Attributes

    @property
    def room_name(self) -> str:
        return self._room_name

    @property
    def message_id(self) -> str:
        return self._message_id

    @property
    def parent_id(self) -> Optional[str]:
        return self._parent_id

    @property
    def previous_edit_id(self) -> Optional[str]:
        return self._previous_edit_id

    @property
    def time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp)

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @property
    def sender(self) -> Session:
        return self._sender

    @property
    def content(self) -> str:
        return self._content

    @property
    def encryption_key_id(self) -> Optional[str]:
        return self._encryption_key_id

    @property
    def edited_time(self) -> Optional[datetime.datetime]:
        if self.edited_timestamp is not None:
            return datetime.datetime.fromtimestamp(self.edited_timestamp)
        else:
            return None

    @property
    def edited_timestamp(self) -> Optional[int]:
        return self._edited_timestamp

    @property
    def deleted_time(self) -> Optional[datetime.datetime]:
        if self.deleted_timestamp is not None:
            return datetime.datetime.fromtimestamp(self.deleted_timestamp)
        else:
            return None

    @property
    def deleted_timestamp(self) -> Optional[int]:
        return self._deleted_timestamp

    @property
    def truncated(self) -> bool:
        return self._truncated

class LiveMessage(Message):
    def __init__(self,
            room: "Room",
            message_id: str,
            parent_id: Optional[str],
            previous_edit_id: Optional[str],
            timestamp: int,
            sender: LiveSession,
            content: str,
            encryption_key_id: Optional[str],
            edited_timestamp: Optional[int],
            deleted_timestamp: Optional[int],
            truncated: bool
            ) -> None:
        super().__init__(room.name, message_id, parent_id, previous_edit_id,
                timestamp, sender, content, encryption_key_id,
                edited_timestamp, deleted_timestamp, truncated)
        self._room = room
        self._live_sender = sender

    @classmethod
    def from_data(cls, # type: ignore
            room: "Room",
            data: Any
            ) -> "LiveMessage":
        return cls.from_message(room, Message.from_data(room.name, data))

    @classmethod
    def from_message(cls, room: "Room", message: Message) -> "LiveMessage":
        live_sender = LiveSession.from_session(room, message.sender)
        return cls(room, message.message_id, message.parent_id,
                message.previous_edit_id, message.timestamp, live_sender,
                message.content, message.encryption_key_id,
                message.edited_timestamp, message.deleted_timestamp,
                message.truncated)

    # Attributes

    @property
    def room(self) -> "Room":
        return self._room

    @property
    def sender(self) -> LiveSession:
        return self._live_sender

    # Live stuff

    async def reply(self, content: str) -> "LiveMessage":
        return await self.room.send(content, parent_id=self.message_id)

    async def before(self, amount: int) -> List["LiveMessage"]:
        return await self.room.log(amount, before_id=self.message_id)
