from typing import TYPE_CHECKING, Any, Iterator, Optional

if TYPE_CHECKING:
    from .room import Room

__all__ = ["Account", "Session", "LiveSession", "LiveSessionListing"]

class Account:
    pass

    @classmethod
    def from_data(cls, data: Any) -> "Account":
        pass

class Session:
    pass

    @property
    def nick(self) -> str:
        pass

    @property
    def session_id(self) -> str:
        pass

class LiveSession(Session):
    pass

    @classmethod
    def from_data(cls, room: "Room", data: Any) -> "LiveSession":
        pass

    @property
    def server_id(self) -> str:
        pass

    @property
    def server_era(self) -> str:
        pass

    def with_nick(self, nick: str) -> "LiveSession":
        pass

class LiveSessionListing:
    pass

    def __iter__(self) -> Iterator[LiveSession]:
        pass

    @classmethod
    def from_data(cls,
            room: "Room",
            data: Any,
            exclude_id: Optional[str] = None
            ) -> "LiveSessionListing":
        pass

    def get(self, session_id: str) -> Optional[LiveSession]:
        pass

    def with_join(self, session: LiveSession) -> "LiveSessionListing":
        pass

    def with_part(self, session: LiveSession) -> "LiveSessionListing":
        pass

    def with_nick(self,
            session: LiveSession,
            new_nick: str
            ) -> "LiveSessionListing":
        pass
