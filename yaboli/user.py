from .util import mention, atmention

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client
    from .room import Room

__all__ = ["User", "LiveUser"]

class User:
    def __init__(self,
            room_name: str,
            id_: str,
            name: str,
            is_staff: bool,
            is_manager: bool):
        self._room_name = room_name
        self._id = id_
        self._name = name
        self._is_staff = is_staff
        self._is_manager = is_manager

    @property
    def room_name(self) -> str:
        return self._room_name

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        # no name = empty str
        return self._name

    @property
    def is_staff(self) -> bool:
        return self._is_staff

    @property
    def is_manager(self) -> bool:
        return self._is_manager

    @property
    def is_account(self) -> bool:
        pass

    @property
    def is_agent(self) -> bool:
        # TODO should catch all old ids too
        pass

    @property
    def is_bot(self) -> bool:
        pass

    # TODO possibly add other fields

    # Properties here? Yeah sure, why not?

    @property
    def mention(self) -> str:
        return mention(self.name)

    @property
    def atmention(self) -> str:
        return atmention(self.name)

class LiveUser(User):
    def __init__(self,
            client: 'Client',
            room: 'Room',
            id_: str,
            name: str,
            is_staff: bool,
            is_manager: bool):
        super().__init__(room.name, id_, name, is_staff, is_manager)
        self._room = room

    @property
    def room(self) -> 'Room':
        return self._room

    # NotLoggedInException
    async def pm(self) -> 'Room':
        pass

    # kick
    # ban
    # ip_ban
