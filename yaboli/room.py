from typing import List, Optional

from .exceptions import *
from .message import LiveMessage
from .user import LiveUser

__all__ = ["Room"]

class Room:
    """
    A Room represents one connection to a room on euphoria, i. e. what other
    implementations might consider a "client". This means that each Room has
    its own session (User) and nick.

    A Room can only be used once in the sense that after it has been closed,
    any further actions will result in a RoomClosedException. If you need to
    manually reconnect, instead just create a new Room object.



    Life cycle of a Room

    1. create a new Room and register callbacks
    2. await join()
    3. do room-related stuff
    4. await part()



    IN PHASE 1, a password and a starting nick can be set. The password and
    current nick are used when first connecting to the room, or when
    reconnecting to the room after connection was lost.

    Usually, event callbacks are also registered during this phase.



    IN PHASE 2, the Room creates the initial connection to euphoria and
    performs initialisations (i. e. authentication or setting the nick) where
    necessary. It also starts the Room's main event loop. The join() function
    returns once one of the following cases has occurred:

    1. the room is now in phase 3, in which case join() returns None
    2. the room could not be joined, in which case one of the JoinExceptions is
       returned



    IN PHASE 3, the usual room-related functions like say() or nick() are
    available. The Room's event loop is running.

    The room will automatically reconnect if it loses connection to euphoria.
    The usual room-related functions will block until the room has successfully
    reconnected.



    IN PHASE 4, the Room is disconnected and the event loop stopped. During and
    after completion of this phase, the Room is considered closed. Any further
    attempts to re-join or call room action functions will result in a
    RoomClosedException.
    """

    # Phase 1

    def __init__(self,
            room_name: str,
            nick: str = "",
            password: Optional[str] = None) -> None:
        pass

        self.closed = False

    # Phase 2

    # Phase 3

    def _ensure_open(self) -> None:
        if self.closed:
            raise RoomClosedException()

    async def _ensure_joined(self) -> None:
        pass

    async def _ensure(self) -> None:
        self._ensure_open()
        await self._ensure_joined()

    # Phase 4

    # Other stuff

    @property
    def name(self) -> str:
        pass

    async def say(self,
            text: str,
            parent_id: Optional[str] = None
            ) -> LiveMessage:
        pass

    @property
    def users(self) -> List[LiveUser]:
        pass

    # retrieving messages
