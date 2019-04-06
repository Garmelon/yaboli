import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

import websockets

from .events import Events
from .exceptions import *

logger = logging.getLogger(__name__)

__all__ = ["Connection"]

class Connection:
    """
    The Connection handles the lower-level stuff required when connecting to
    euphoria, such as:

    - Creating a websocket connection
    - Encoding and decoding packets (json)
    - Waiting for the server's asynchronous replies to packets
    - Keeping the connection alive (ping, ping-reply packets)
    - Reconnecting (timeout while connecting, no pings received in some time)



    Life cycle of a Connection:

    1. create connection and register event callbacks
    2. call connect()
    3. send and receive packets, reconnecting automatically when connection is
    lost
    4. call disconnect(), then go to 2.


    IN PHASE 1, parameters such as the url the Connection should connect to are
    set. Usually, event callbacks are also registered in this phase.


    IN PHASE 2, the Connection attempts to connect to the url set in phase 1.
    If successfully connected, it fires a "connected" event.


    IN PHASE 3, the Connection listenes for packets from the server and fires
    the corresponding events. Packets can be sent using the Connection.

    If the Connection has to reconnect for some reason, it first fires a
    "reconnecting" event. Then it tries to reconnect until it has established a
    connection to euphoria again. After the connection is reestablished, it
    fires a "reconnected" event.


    IN PHASE 4, the Connection fires a "disconnecting" event and then closes
    the connection to euphoria. This event is the last event that is fired
    until connect() is called again.



    Events:

    - "connected" : No arguments
    - "reconnecting" : No arguments
    - "reconnected" : No arguments
    - "disconnecting" : No arguments
    - "on_<euph event name>": the packet, parsed as JSON

    Events ending with "-ing" ("reconnecting", "disconnecting") are fired at
    the beginning of the process they represent. Events ending with "-ed"
    ("connected", "reconnected") are fired after the process they represent has
    finished.

    Examples for the last category of events include "on_message-event",
    "on_part-event" and "on_ping".
    """

    # Maximum duration between euphoria's ping messages
    PING_TIMEOUT = 60 # seconds

    _NOT_RUNNING = "not running"
    _CONNECTING = "connecting"
    _RUNNING = "running"
    _RECONNECTING = "reconnecting"
    _DISCONNECTING = "disconnecting"

    # Initialising

    def __init__(self, url: str) -> None:
        self._url = url

        self._events = Events()

        # This is the current status of the connection. It can be set to one of
        # _NOT_RUNNING, _CONNECTING, _RUNNING, _RECONNECTING, or
        # _DISCONNECTING.
        #
        # Always be careful to set any state-dependent variables.
        self._state = self._NOT_RUNNING
        self._connected_condition = asyncio.Condition()
        self._disconnected_condition = asyncio.Condition()

        self._event_loop: Optional[asyncio.Task[None]] = None

        # These must always be (re)set together. If one of them is None, all
        # must be None.
        self._ws = None
        self._awaiting_replies: Optional[Dict[str, Callable[...,
            Awaitable[None]]]] = None
        self._ping_check: Optional[asyncio.Task[None]] = None

    def register_event(self,
            event: str,
            callback: Callable[..., Awaitable[None]]
            ) -> None:
        self._events.register(event, callback)

    # Connecting and disconnecting

    async def _disconnect(self) -> None:
        """
        Disconnect _ws and clean up _ws, _awaiting_replies and _ping_check.

        Important: The caller must ensure that this function is called in valid
        circumstances and not called twice at the same time. _disconnect() does
        not check or manipulate _state.
        """

        if self._ws is None:
            # This indicates that _ws, _awaiting_replies and _ping_check are
            # cleaned up
            return

        await self._ws.close()

        for tasks in self._awaiting_replies.values():
            for task in tasks:
                task.cancel()

        self._ping_check.cancel()

        self._ws = None
        self._awaiting_replies = None
        self._ping_check = None

    async def _connect(self) -> bool:
        """
        Attempts once to create a ws connection.

        Important: The caller must ensure that this function is called in valid
        circumstances and not called twice at the same time. _connect() does
        not check or manipulate _state, nor does it perform cleanup on
        _awaiting_replies or _ping_check.
        """

        try:
            ws = await websockets.connect(self._url)

            self._ws = ws
            self._awaiting_replies = {}
            self._ping_check = asyncio.create_task(
                    self._disconnect_in(self.PING_TIMEOUT))

            return True

        # TODO list all of the ways that creating a connection can go wrong
        except websockets.InvalidStatusCode:
            return False

    async def _disconnect_in(self, delay: int) -> None:
        await asyncio.sleep(delay)
        await self._disconnect()

    async def connect(self) -> bool:
        # Special exception message for _CONNECTING.
        if self._state == self._CONNECTING:
            raise IncorrectStateException(("connect() may not be called"
                " multiple times."))

        if self._state != self._NOT_RUNNING:
            raise IncorrectStateException(("disconnect() must complete before"
                " connect() may be called again."))

        # Now we're sure we're in the _NOT_RUNNING state, we can set our state.
        # Important: No await-ing has occurred between checking the state and
        # setting it.
        self._state = self._CONNECTING

        if await self._connect():
            self._event_loop = asyncio.create_task(self._run())
            self._state = self._RUNNING

            async with self._connected_condition:
                self._connected_condition.notify_all()

            return True
        else:
            self._state = self._NOT_RUNNING

            async with self._connected_condition:
                self._connected_condition.notify_all()

            return False

    async def _reconnect(self) -> bool:
        """
        This function should only be called from the event loop while the
        _state is _RUNNING.
        """

        if self._state != self._RUNNING:
            raise IncorrectStateException()

        self._state = self._RECONNECTING

        await self._disconnect()
        success =  await self._connect()

        self._state = self._RUNNING
        async with self._connected_condition:
            self._connected_condition.notify_all()

        return success

    async def disconnect(self) -> None:
        # This function is kinda complex. The comments make it harder to read,
        # but hopefully easier to understand.

        # Possible states left: _NOT_RUNNING, _CONNECTING, _RUNNING,
        # _RECONNECTING, _DISCONNECTING

        # Waiting until the current connection attempt is finished.
        if self._state in [self._CONNECTING, self._RECONNECTING]:
            # After _CONNECTING, the state can either be _NOT_RUNNING or
            # _RUNNING. After _RECONNECTING, the state must be _RUNNING.
            async with self._connected_condition:
                await self._connected_condition.wait()
            # The state is now either _NOT_RUNNING or _RUNNING.

        # Possible states left: _NOT_RUNNING, _RUNNING, _DISCONNECTING

        if self._state == self._NOT_RUNNING:
            # No need to do anything since we're already disconnected
            return

        # Possible states left: _RUNNING, _DISCONNECTING

        if self._state == self._DISCONNECTING:
            # Wait until the disconnecting currently going on is complete. This
            # is to prevent the disconnect() function from ever returning
            # without the disconnecting process being finished.
            async with self._disconnected_condition:
                await self._disconnected_condition.wait()

            return

        # Possible states left: _RUNNING

        # By principle of exclusion, the only state left is _RUNNING. Doing an
        # explicit check though, just to make sure.
        if self._state != self._RUNNING:
            raise IncorrectStateException("This should never happen.")

        # Now we're sure we're in the _RUNNING state, we can set our state.
        # Important: No await-ing has occurred between checking the state and
        # setting it.
        self._state = self._DISCONNECTING

        await self._disconnect()

        # We know that _event_loop is not None, but this is to keep mypy happy.
        if self._event_loop is not None:
            await self._event_loop
            self._event_loop = None

        self._state = self._NOT_RUNNING

        # Notify all other disconnect()s waiting
        async with self._disconnected_condition:
            self._disconnected_condition.notify_all()

    # Running

    async def _run(self) -> None:
        """
        The main loop that runs during phase 3
        """

        # TODO

    async def send(self, packet: Any) -> Any:
        pass # TODO
