import re
from typing import TYPE_CHECKING, Any, Dict, Iterable, Iterator, List, Optional

from .util import mention, normalize

if TYPE_CHECKING:
    from .room import Room

__all__ = ["Account", "Session", "LiveSession", "LiveSessionListing"]

class Account:
    """
    This class represents a http://api.euphoria.io/#personalaccountview, with a
    few added fields stolen from the hello-event (see
    http://api.euphoria.io/#hello-event).
    """

    def __init__(self,
            account_id: str,
            name: str,
            email: str,
            has_access: Optional[bool],
            email_verified: Optional[bool]
            ) -> None:
        self._account_id = account_id
        self._name = name
        self._email = email
        self._has_access = has_access
        self._email_verified = email_verified

    @classmethod
    def from_data(cls, data: Any) -> "Account":
        """
        The data parameter must be the "data" part of a hello-event.

        If, in the future, a PersonalAccountView appears in other places, this
        function might have to be changed.
        """

        view = data["account"]

        account_id = view["id"]
        name = view["name"]
        email = view["email"]

        has_access = data.get("account_has_access")
        email_verified = data.get("account_email_verified")

        return cls(account_id, name, email, has_access, email_verified)

    # Attributes

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def has_access(self) -> Optional[bool]:
        return self._has_access

    @property
    def email_verified(self) -> Optional[bool]:
        return self._email_verified

class Session:
    _ID_SPLIT_RE = re.compile(r"(agent|account|bot):(.*)")

    def __init__(self,
            room_name: str,
            user_id: str,
            nick: str,
            server_id: str,
            server_era: str,
            session_id: str,
            is_staff: bool,
            is_manager: bool,
            client_address: Optional[str]
            ) -> None:
        self._room_name = room_name
        self._user_id = user_id

        self._id_type: Optional[str]
        match = self._ID_SPLIT_RE.fullmatch(self._user_id)
        if match is not None:
            self._id_type = match.group(1)
        else:
            self._id_type = None

        self._nick = nick
        self._server_id = server_id
        self._server_era = server_era
        self._session_id = session_id
        self._is_staff = is_staff
        self._is_manager = is_manager
        self._client_address = client_address

    def _copy(self) -> "Session":
        return Session(self.room_name, self.user_id, self.nick, self.server_id,
                self.server_era, self.session_id, self.is_staff,
                self.is_manager, self.client_address)

    @classmethod
    def from_data(cls, room_name: str, data: Any) -> "Session":
        user_id = data["id"]
        nick = data["name"]
        server_id = data["server_id"]
        server_era = data["server_era"]
        session_id = data["session_id"]
        is_staff = data["is_staff"]
        is_manager = data["is_manager"]
        client_address = data.get("client_address")

        return cls(room_name, user_id, nick, server_id, server_era, session_id,
                is_staff, is_manager, client_address)

    def with_nick(self, nick: str) -> "Session":
        copy = self._copy()
        copy._nick = nick
        return copy

    # Attributes

    @property
    def room_name(self) -> str:
        return self._room_name

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def nick(self) -> str:
        return self._nick

    @property
    def server_id(self) -> str:
        return self._server_id

    @property
    def server_era(self) -> str:
        return self._server_era

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def is_staff(self) -> bool:
        return self._is_staff

    @property
    def is_manager(self) -> bool:
        return self._is_manager

    @property
    def client_address(self) -> Optional[str]:
        return self._client_address

    @property
    def mention(self) -> str:
        return mention(self.nick, ping=False)

    @property
    def atmention(self) -> str:
        return mention(self.nick, ping=True)

    @property
    def normalize(self) -> str:
        return normalize(self.nick)

    @property
    def is_person(self) -> bool:
        return self._id_type is None or self._id_type in ["agent", "account"]

    @property
    def is_agent(self) -> bool:
        return self._id_type == "agent"

    @property
    def is_account(self) -> bool:
        return self._id_type == "account"

    @property
    def is_bot(self) -> bool:
        return self._id_type == "bot"

class LiveSession(Session):
    def __init__(self,
            room: "Room",
            user_id: str,
            nick: str,
            server_id: str,
            server_era: str,
            session_id: str,
            is_staff: bool,
            is_manager: bool,
            client_address: Optional[str]
            ) -> None:
        super().__init__(room.name, user_id, nick, server_id, server_era,
                session_id, is_staff, is_manager, client_address)
        self._room = room

    def _copy(self) -> "LiveSession":
        return self.from_session(self._room, self)

    # Ignoring the type discrepancy since it is more convenient this way
    @classmethod
    def from_data(cls, # type: ignore
            room: "Room",
            data: Any
            ) -> "LiveSession":
        return cls.from_session(room, Session.from_data(room.name, data))

    @classmethod
    def from_session(cls, room: "Room", session: Session) -> "LiveSession":
        return cls(room, session.user_id, session.nick, session.server_id,
                session.server_era, session.session_id, session.is_staff,
                session.is_manager, session.client_address)

    def with_nick(self, nick: str) -> "LiveSession":
        copy = self._copy()
        copy._nick = nick
        return copy

    # Attributes

    @property
    def room(self) -> "Room":
        return self._room

    # Live stuff

    # TODO pm, once pm support is there.

class LiveSessionListing:
    def __init__(self, room: "Room", sessions: Iterable[LiveSession]) -> None:
        self._room = room
        # just to make sure it doesn't get changed on us
        self._sessions: Dict[str, LiveSession] = {session.session_id: session
                for session in sessions}

    def __iter__(self) -> Iterator[LiveSession]:
        return self._sessions.values().__iter__()

    def _copy(self) -> "LiveSessionListing":
        return LiveSessionListing(self.room, self)

    @classmethod
    def from_data(cls,
            room: "Room",
            data: Any,
            exclude_id: Optional[str] = None
            ) -> "LiveSessionListing":
        sessions = [LiveSession.from_data(room, subdata) for subdata in data]

        if exclude_id:
            sessions = [session for session in sessions
                    if session.session_id != exclude_id]

        return cls(room, sessions)

    def get(self, session_id: str) -> Optional[LiveSession]:
        return self._sessions.get(session_id)

    def with_join(self, session: LiveSession) -> "LiveSessionListing":
        copy = self._copy()
        copy._sessions[session.session_id] = session
        return copy

    def with_part(self, session: LiveSession) -> "LiveSessionListing":
        copy = self._copy()

        if session.session_id in copy._sessions:
            del copy._sessions[session.session_id]

        return copy

    def with_nick(self,
            session: LiveSession,
            new_nick: str
            ) -> "LiveSessionListing":
        copy = self._copy()
        copy._sessions[session.session_id] = session.with_nick(new_nick)
        return copy

    # Attributes

    @property
    def room(self) -> "Room":
        return self._room

    @property
    def all(self) -> List[LiveSession]:
        return list(self._sessions.values())

    @property
    def people(self) -> List[LiveSession]:
        return [session for session in self if session.is_person]

    @property
    def accounts(self) -> List[LiveSession]:
        return [session for session in self if session.is_account]

    @property
    def agents(self) -> List[LiveSession]:
        return [session for session in self if session.is_agent]

    @property
    def bots(self) -> List[LiveSession]:
        return [session for session in self if session.is_bot]
