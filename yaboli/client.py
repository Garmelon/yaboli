import asyncio
import functools
import logging
from typing import Dict, List, Optional, Union

from .message import LiveMessage
from .room import Room
from .session import LiveSession

logger = logging.getLogger(__name__)

__all__ = ["Client"]

class Client:
    def __init__(self,
            default_nick: str,
            cookie_file: Optional[str] = None,
            ) -> None:
        self._default_nick = default_nick
        self._cookie_file = cookie_file
        self._rooms: Dict[str, List[Room]] = {}
        self._stop = asyncio.Event()

    async def run(self) -> None:
        await self.started()
        await self._stop.wait()

    async def stop(self) -> None:
        await self.stopping()

        tasks = []
        for rooms in self._rooms.values():
            for room in rooms:
                tasks.append(asyncio.create_task(self.part(room)))
        for task in tasks:
            await task

        self._stop.set()

    # Managing rooms

    def get(self, room_name: str) -> Optional[Room]:
        rooms = self._rooms.get(room_name)
        if rooms: # None or [] are False-y
            return rooms[0]
        else:
            return None

    def get_all(self, room_name: str) -> List[Room]:
        return self._rooms.get(room_name, [])

    async def join(self,
            room_name: str,
            password: Optional[str] = None,
            nick: Optional[str] = None,
            cookie_file: Union[str, bool] = True,
            ) -> Optional[Room]:
        """
        cookie_file is the name of the file to store the cookies in. If it is
        True, the client default is used. If it is False, no cookie file name
        will be used.
        """

        logger.info(f"Joining &{room_name}")

        if nick is None:
            nick = self._default_nick

        this_cookie_file: Optional[str]

        if isinstance(cookie_file, str): # This way, mypy doesn't complain
            this_cookie_file = cookie_file
        elif cookie_file:
            this_cookie_file = self._cookie_file
        else:
            this_cookie_file = None

        room = Room(room_name, password=password, target_nick=nick,
                cookie_file=this_cookie_file)

        room.register_event("connected",
                functools.partial(self.on_connected, room))
        room.register_event("snapshot",
                functools.partial(self.on_snapshot, room))
        room.register_event("send",
                functools.partial(self.on_send, room))
        room.register_event("join",
                functools.partial(self.on_join, room))
        room.register_event("part",
                functools.partial(self.on_part, room))
        room.register_event("nick",
                functools.partial(self.on_nick, room))
        room.register_event("edit",
                functools.partial(self.on_edit, room))
        room.register_event("pm",
                functools.partial(self.on_pm, room))
        room.register_event("disconnect",
                functools.partial(self.on_disconnect, room))

        if await room.connect():
            rooms = self._rooms.get(room_name, [])
            rooms.append(room)
            self._rooms[room_name] = rooms

            return room
        else:
            logger.warn(f"Could not join &{room.name}")
            return None

    async def part(self, room: Room) -> None:
        logger.info(f"Leaving &{room.name}")

        rooms = self._rooms.get(room.name, [])
        rooms = [r for r in rooms if r is not room]
        self._rooms[room.name] = rooms

        await room.disconnect()

    # Management stuff - overwrite these functions

    async def started(self) -> None:
        pass

    async def stopping(self) -> None:
        pass

    # Event stuff - overwrite these functions

    async def on_connected(self, room: Room) -> None:
        pass

    async def on_snapshot(self, room: Room, messages: List[LiveMessage]) -> None:
        pass

    async def on_send(self, room: Room, message: LiveMessage) -> None:
        pass

    async def on_join(self, room: Room, user: LiveSession) -> None:
        pass

    async def on_part(self, room: Room, user: LiveSession) -> None:
        pass

    async def on_nick(self,
            room: Room,
            user: LiveSession,
            from_nick: str,
            to_nick: str
            ) -> None:
        pass

    async def on_edit(self, room: Room, message: LiveMessage) -> None:
        pass

    async def on_login(self, room: Room, account_id: str) -> None:
        pass

    async def on_logout(self, room: Room) -> None:
        pass

    async def on_pm(self,
            room: Room,
            from_id: str,
            from_nick: str,
            from_room: str,
            pm_id: str
            ) -> None:
        pass

    async def on_disconnect(self, room: Room, reason: str) -> None:
        pass
