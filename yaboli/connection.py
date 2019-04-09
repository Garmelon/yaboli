import asyncio
import json
import logging
import socket
from typing import Any, Awaitable, Callable, Dict, Optional

import websockets

from .events import Events
from .exceptions import *

logger = logging.getLogger(__name__)

__all__ = ["Connection"]

# This class could probably be cleaned up by introducing one or two well-placed
# Locks – something for the next rewrite :P

class Connection:
    """
    The Connection handles the lower-level stuff required when connecting to
    euphoria, such as:

    - Creating a websocket connection
    - Encoding and decoding packets (json)
    - Waiting for the server's asynchronous replies to packets
    - Keeping the connection alive (ping, ping-reply packets)
    - Reconnecting (timeout while connecting, no pings received in some time)

    It doesn't respond to any events other than the ping-event and is otherwise
    "dumb".



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
    - "<euph event name>": the packet, parsed as JSON

    Events ending with "-ing" ("reconnecting", "disconnecting") are fired at
    the beginning of the process they represent. Events ending with "-ed"
    ("connected", "reconnected") are fired after the process they represent has
    finished.

    Examples for the last category of events include "message-event",
    "part-event" and "ping".
    """

    # Maximum duration between euphoria's ping messages. Euphoria usually sends
    # ping messages every 20 to 30 seconds.
    PING_TIMEOUT = 40 # seconds

    # The delay between reconnect attempts.
    RECONNECT_DELAY = 40 # seconds

    # States the Connection may be in
    _NOT_RUNNING = "not running"
    _CONNECTING = "connecting"
    _RUNNING = "running"
    _RECONNECTING = "reconnecting"
    _DISCONNECTING = "disconnecting"

    # Initialising

    def __init__(self, url: str) -> None:
        self._url = url

        self._events = Events()
        self._packet_id = 0

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
        self._awaiting_replies: Optional[Dict[str, asyncio.Future[Any]]] = None
        self._ping_check: Optional[asyncio.Task[None]] = None

        self.register_event("ping-event", self._ping_pong)

    def register_event(self,
            event: str,
            callback: Callable[..., Awaitable[None]]
            ) -> None:
        """
        Register an event callback.

        For an overview of the possible events, see the Connection docstring.
        """

        self._events.register(event, callback)

    # Connecting and disconnecting

    async def _disconnect(self) -> None:
        """
        Disconnect _ws and clean up _ws, _awaiting_replies and _ping_check.

        Important: The caller must ensure that this function is called in valid
        circumstances and not called twice at the same time. _disconnect() does
        not check or manipulate _state.
        """

        if self._ws is not None:
            logger.debug("Closing ws connection")
            await self._ws.close()

        # Checking self._ws again since during the above await, another
        # disconnect call could have finished cleaning up.
        if self._ws is None:
            # This indicates that _ws, _awaiting_replies and _ping_check are
            # cleaned up
            logger.debug("Ws connection already cleaned up")
            return

        logger.debug("Cancelling futures waiting for replies")
        for future in self._awaiting_replies.values():
            future.set_exception(ConnectionClosedException())

        logger.debug("Cancelling ping check task")
        self._ping_check.cancel()

        logger.debug("Cleaning up variables")
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
            logger.debug(f"Creating ws connection to {self._url!r}")
            ws = await websockets.connect(self._url)

            self._ws = ws
            self._awaiting_replies = {}
            logger.debug("Starting ping check")
            self._ping_check = asyncio.create_task(
                    self._disconnect_in(self.PING_TIMEOUT))

            return True

        except (websockets.InvalidHandshake, websockets.InvalidStatusCode,
                socket.gaierror):
            logger.debug("Connection failed")
            return False

    async def _disconnect_in(self, delay: int) -> None:
        await asyncio.sleep(delay)
        logger.debug(f"Disconnect timeout of {delay}s elapsed, disconnecting...")
        # Starting the _disconnect function in another task because otherwise,
        # its own CancelledError would inhibit _disconnect() from completing
        # the disconnect.
        #
        # We don't need to check the state because _disconnect_in only runs
        # while the _state is _RUNNING.
        asyncio.create_task(self._disconnect())

    async def _reconnect(self) -> bool:
        """
        This function should only be called from the event loop while the
        _state is _RUNNING.
        """

        if self._state != self._RUNNING:
            raise IncorrectStateException("This should never happen")

        logger.debug("Reconnecting...")
        self._events.fire("reconnecting")
        self._state = self._RECONNECTING

        await self._disconnect()
        success =  await self._connect()

        self._state = self._RUNNING
        self._events.fire("reconnected")

        logger.debug("Sending connected notification")
        async with self._connected_condition:
            self._connected_condition.notify_all()

        logger.debug("Reconnected" if success else "Reconnection failed")
        return success

    async def connect(self) -> bool:
        """
        Attempt to create a connection to the Connection's url.

        Returns True if the Connection could connect to the url and is now
        running. Returns False if the Connection could not connect to the url
        and is not running.

        Exceptions:

        This function must be called while the connection is not running,
        otherwise an IncorrectStateException will be thrown. To stop a
        Connection, use disconnect().
        """

        # Special exception message for _CONNECTING.
        if self._state == self._CONNECTING:
            raise IncorrectStateException(("connect() may not be called"
                " multiple times."))

        if self._state != self._NOT_RUNNING:
            raise IncorrectStateException(("disconnect() must complete before"
                " connect() may be called again."))

        logger.debug("Connecting...")

        # Now we're sure we're in the _NOT_RUNNING state, we can set our state.
        # Important: No await-ing has occurred between checking the state and
        # setting it.
        self._state = self._CONNECTING

        success = await self._connect()

        if success:
            logger.debug("Starting event loop")
            self._event_loop = asyncio.create_task(self._run())
            self._state = self._RUNNING
            self._events.fire("connected")
        else:
            self._state = self._NOT_RUNNING

        logger.debug("Sending connected notification")
        async with self._connected_condition:
            self._connected_condition.notify_all()

        logger.debug("Connected" if success else "Connection failed")
        return success

    async def disconnect(self) -> None:
        """
        Close and stop the Connection, if it is currently (re-)connecting or
        running. Does nothing if the Connection is not running.

        This function returns once the Connection has stopped running.
        """

        # Possible states left: _NOT_RUNNING, _CONNECTING, _RUNNING,
        # _RECONNECTING, _DISCONNECTING

        # Waiting until the current connection attempt is finished. Using a
        # while loop since the event loop might have started to reconnect again
        # while the await is still waiting.
        while self._state in [self._CONNECTING, self._RECONNECTING]:
            # After _CONNECTING, the state can either be _NOT_RUNNING or
            # _RUNNING. After _RECONNECTING, the state must be _RUNNING.
            async with self._connected_condition:
                await self._connected_condition.wait()

        # Possible states left: _NOT_RUNNING, _RUNNING, _DISCONNECTING

        if self._state == self._NOT_RUNNING:
            # No need to do anything since we're already disconnected
            logger.debug("Already disconnected")
            return

        # Possible states left: _RUNNING, _DISCONNECTING

        if self._state == self._DISCONNECTING:
            # Wait until the disconnecting currently going on is complete. This
            # is to prevent the disconnect() function from ever returning
            # without the disconnecting process being finished.
            logger.debug("Already disconnecting, waiting for it to finish...")
            async with self._disconnected_condition:
                await self._disconnected_condition.wait()

            logger.debug("Disconnected, finished waiting")
            return

        # Possible states left: _RUNNING

        # By principle of exclusion, the only state left is _RUNNING. Doing an
        # explicit check though, just to make sure.
        if self._state != self._RUNNING:
            raise IncorrectStateException("This should never happen.")


        logger.debug("Disconnecting...")
        self._events.fire("disconnecting")

        # Now we're sure we're in the _RUNNING state, we can set our state.
        # Important: No await-ing has occurred between checking the state and
        # setting it.
        self._state = self._DISCONNECTING

        await self._disconnect()

        # We know that _event_loop is not None, but this is to keep mypy happy.
        logger.debug("Waiting for event loop")
        if self._event_loop is not None:
            await self._event_loop
            self._event_loop = None

        self._state = self._NOT_RUNNING

        # Notify all other disconnect()s waiting
        logger.debug("Sending disconnected notification")
        async with self._disconnected_condition:
            self._disconnected_condition.notify_all()

        logger.debug("Disconnected")

    async def reconnect(self) -> None:
        """
        Forces the Connection to reconnect.

        This function may return before the reconnect process is finished.

        Exceptions:

        This function must be called while the connection is (re-)connecting or
        running, otherwise an IncorrectStateException will be thrown.
        """

        if self._state in [self._CONNECTING, self._RECONNECTING]:
            logger.debug("Already (re-)connecting, waiting for it to finish...")
            async with self._connected_condition:
                await self._connected_condition.wait()

            logger.debug("(Re-)connected, finished waiting")
            return

        if self._state != self._RUNNING:
            raise IncorrectStateException(("reconnect() may not be called while"
                " the connection is not running."))

        # Disconnecting via task because otherwise, the _connected_condition
        # might fire before we start waiting for it.
        #
        # The event loop will reconenct after the ws connection has been
        # disconnected.
        logger.debug("Disconnecting and letting the event loop reconnect")
        await self._disconnect()

    # Running

    async def _run(self) -> None:
        """
        The main loop that runs during phase 3
        """

        while True:
            # The "Exiting event loop" checks are a bit ugly. They're in place
            # so that the event loop exits on its own at predefined positions
            # instead of randomly getting thrown a CancelledError.
            #
            # Now that I think about it, the whole function looks kinda ugly.
            # Maybe one day (yeah, right), I'll clean this up. I want to get it
            # working first though.

            if self._state != self._RUNNING:
                logger.debug("Exiting event loop")
                return

            if self._ws is not None:
                try:
                    logger.debug("Receiving ws packets")
                    async for packet in self._ws:
                        logger.debug(f"Received packet {packet}")
                        packet_data = json.loads(packet)
                        self._process_packet(packet_data)
                except websockets.ConnectionClosed:
                    logger.debug("Stopped receiving ws packets")
            else:
                logger.debug("No ws connection found")

            if self._state != self._RUNNING:
                logger.debug("Exiting event loop")
                return

            logger.debug("Attempting to reconnect")
            while not await self._reconnect():
                logger.debug("Reconnect attempt not successful")

                if self._state != self._RUNNING:
                    logger.debug("Exiting event loop")
                    return

                logger.debug(f"Sleeping for {self.RECONNECT_DELAY}s and retrying")
                await asyncio.sleep(self.RECONNECT_DELAY)

    def _process_packet(self, packet: Any) -> None:
        # This function assumes that the packet is formed correctly according
        # to http://api.euphoria.io/#packets.

        # First, notify whoever's waiting for this packet
        packet_id = packet.get("id", None)
        if packet_id is not None and self._awaiting_replies is not None:
            future = self._awaiting_replies.get(packet_id, None)
            if future is not None:
                future.set_result(packet)

        # Then, send the corresponding event
        packet_type = packet["type"]
        self._events.fire(packet_type, packet)

        # Finally, reset the ping check
        logger.debug("Resetting ping check")
        if self._ping_check is not None:
            self._ping_check.cancel()
        self._ping_check = asyncio.create_task(
                self._disconnect_in(self.PING_TIMEOUT))

    async def _do_if_possible(self, coroutine: Awaitable[None]) -> None:
        """
        Try to run a coroutine, ignoring any IncorrectStateExceptions.
        """
        try:
            await coroutine
        except IncorrectStateException:
            pass

    async def _send_if_possible(self, packet_type: str, data: Any,) -> None:
        """
        This function tries to send a packet without awaiting the reply.

        It ignores IncorrectStateExceptions, meaning that if it is called while
        in the wrong state, nothing will happen.
        """

        try:
            await self.send(packet_type, data, await_reply=False)
        except IncorrectStateException:
            logger.debug("Could not send (disconnecting or already disconnected)")

    async def _ping_pong(self, packet: Any) -> None:
        """
        Implements http://api.euphoria.io/#ping and is called as "ping-event"
        callback.
        """
        logger.debug("Pong!")
        await self._do_if_possible(self.send(
            "ping-reply",
            {"time": packet["data"]["time"]},
            await_reply=False
        ))

    async def send(self,
            packet_type: str,
            data: Any,
            await_reply: bool = True
            ) -> Any:
        """
        Send a packet of type packet_type to the server.

        The object passed as data will make up the packet's "data" section and
        must be json-serializable.

        This function will return the complete json-deserialized reply package,
        unless await_reply is set to False, in which case it will immediately
        return None.

        Exceptions:

        This function must be called while the Connection is (re-)connecting or
        running, otherwise an IncorrectStateException will be thrown.

        If the connection closes unexpectedly while sending the packet or
        waiting for the reply, a ConnectionClosedException will be thrown.
        """

        while self._state in [self._CONNECTING, self._RECONNECTING]:
            async with self._connected_condition:
                await self._connected_condition.wait()

        if self._state != self._RUNNING:
            raise IncorrectStateException(("send() must be called while the"
            " Connection is running"))

        # We're now definitely in the _RUNNING state

        # Since we're in the _RUNNING state, _ws and _awaiting_replies are not
        # None. This check is to satisfy mypy.
        if self._ws is None or self._awaiting_replies is None:
            raise IncorrectStateException("This should never happen")

        packet_id = str(self._packet_id)
        self._packet_id += 1

        # Doing this before the await below since we know that
        # _awaiting_replies is not None while the _state is _RUNNING.
        if await_reply:
            response: asyncio.Future[Any] = asyncio.Future()
            self._awaiting_replies[packet_id] = response

        text = json.dumps({"id": packet_id, "type": packet_type, "data": data})
        logger.debug(f"Sending packet {text}")
        try:
            await self._ws.send(text)
        except websockets.ConnectionClosed:
            raise ConnectionClosedException() # as promised in the docstring

        if await_reply:
            await response
            # If the response Future was completed with a
            # ConnectionClosedException via set_exception(), response.result()
            # will re-raise that exception.
            return response.result()
        else:
            return None
