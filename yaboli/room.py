import asyncio
import logging
from typing import Any, Awaitable, Callable, List, Optional, Tuple, TypeVar

from .connection import Connection
from .events import Events
from .exceptions import *
from .message import LiveMessage
from .session import Account, LiveSession, LiveSessionListing
from .util import atmention

logger = logging.getLogger(__name__)

__all__ = ["Room"]

T = TypeVar("T")

class Room:
    """
    Events and parameters:

    "connected" - fired after the Room has authenticated, joined and set its
    nick, meaning that now, messages can be sent
        no parameters

    "snapshot" - snapshot of the room's messages at the time of joining
        messages: List[LiveMessage]

    "send" - another room member has sent a message
        message: LiveMessage

    "join" - somebody has joined the room
        user: LiveSession

    "part" - somebody has left the room
        user: LiveSession

    "nick" - another room member has changed their nick
        user: LiveSession
        from: str
        to: str

    "edit" - a message in the room has been modified or deleted
        message: LiveMessage

    "login" - this session has been logged in from another session
        account_id: str

    "logout" - this session has been logged out from another session
        no parameters

    "pm" - another session initiated a pm with you
        from: str      - the id of the user inviting the client to chat privately
        from_nick: str - the nick of the inviting user
        from_room: str - the room where the invitation was sent from
        pm_id: str     - the private chat can be accessed at /room/pm:PMID

    "disconect" - corresponds to http://api.euphoria.io/#disconnect-event (if
    the reason is "authentication changed", the room automatically reconnects)
        reason: str - the reason for disconnection
    """

    URL_FORMAT = "wss://euphoria.io/room/{}/ws"

    def __init__(self,
            name: str,
            password: Optional[str] = None,
            target_nick: str = "",
            url_format: str = URL_FORMAT,
            cookie_file: Optional[str] = None,
            ) -> None:
        self._name = name
        self._password = password
        self._target_nick = target_nick
        self._url_format = url_format

        self._session: Optional[LiveSession] = None
        self._account: Optional[Account] = None
        self._private: Optional[bool] = None
        self._version: Optional[str] = None
        self._users: Optional[LiveSessionListing] = None
        self._pm_with_nick: Optional[str] = None
        self._pm_with_user_id: Optional[str] = None
        self._server_version: Optional[str] = None

        # Connected management
        self._url = self._url_format.format(self._name)
        self._connection = Connection(self._url, cookie_file=cookie_file)
        self._events = Events()

        self._connected = asyncio.Event()
        self._connected_successfully = False
        self._hello_received = False
        self._snapshot_received = False

        self._connection.register_event("reconnecting", self._on_reconnecting)
        self._connection.register_event("hello-event", self._on_hello_event)
        self._connection.register_event("snapshot-event", self._on_snapshot_event)
        self._connection.register_event("bounce-event", self._on_bounce_event)

        self._connection.register_event("disconnect-event", self._on_disconnect_event)
        self._connection.register_event("join-event", self._on_join_event)
        self._connection.register_event("login-event", self._on_login_event)
        self._connection.register_event("logout-event", self._on_logout_event)
        self._connection.register_event("network-event", self._on_network_event)
        self._connection.register_event("nick-event", self._on_nick_event)
        self._connection.register_event("edit-message-event", self._on_edit_message_event)
        self._connection.register_event("part-event", self._on_part_event)
        self._connection.register_event("pm-initiate-event", self._on_pm_initiate_event)
        self._connection.register_event("send-event", self._on_send_event)

    def register_event(self,
            event: str,
            callback: Callable[..., Awaitable[None]]
            ) -> None:
        """
        Register an event callback.

        For an overview of the possible events, see the Room docstring.
        """

        self._events.register(event, callback)

    # Connecting, reconnecting and disconnecting

    async def _try_set_connected(self) -> None:
        packets_received = self._hello_received and self._snapshot_received
        if packets_received and not self._connected.is_set():
            await self._set_nick_if_necessary()
            self._set_connected()

    async def _set_nick_if_necessary(self) -> None:
        nick_needs_updating = (self._session is None
                or self._target_nick != self._session.nick)

        if self._target_nick and nick_needs_updating:
            await self._nick(self._target_nick)

    def _set_connected(self) -> None:
        self._connected_successfully = True
        self._connected.set()

    def _set_connected_failed(self) -> None:
        if not self._connected.is_set():
            self._connected_successfully = False
            self._connected.set()

    def _set_connected_reset(self) -> None:
        self._connected.clear()
        self._connected_successfully = False
        self._hello_received = False
        self._snapshot_received = False

    async def _on_reconnecting(self) -> None:
        self._set_connected_reset()

    async def _on_hello_event(self, packet: Any) -> None:
        data = packet["data"]

        self._session = LiveSession.from_data(self, data["session"])
        self._private = data["room_is_private"]
        self._version = data["version"]

        if "account" in data:
            self._account = Account.from_data(data)

        self._hello_received = True
        await self._try_set_connected()

    async def _on_snapshot_event(self, packet: Any) -> None:
        data = packet["data"]

        self._server_version = data["version"]
        self._users = LiveSessionListing.from_data(self, data["listing"])
        self._pm_with_nick = data.get("pm_with_nick")
        self._pm_with_user_id = data.get("pm_with_user_id")

        # Update session nick
        nick = data.get("nick")
        if nick is not None and self._session is not None:
            self._session = self.session.with_nick(nick)

        # Send "session" event
        messages = [LiveMessage.from_data(self, msg_data)
                for msg_data in data["log"]]
        self._events.fire("session", messages)

        self._snapshot_received = True
        await self._try_set_connected()

    async def _on_bounce_event(self, packet: Any) -> None:
        data = packet["data"]

        # Can we even authenticate? (Assuming that passcode authentication is
        # available if no authentication options are given: Euphoria doesn't
        # (always) send authentication options, even when passcode
        # authentication works.)
        if not "passcode" in data.get("auth_options", ["passcode"]):
            self._set_connected_failed()
            return

        # If so, do we have a password?
        if self._password is None:
            self._set_connected_failed()
            return

        reply = await self._connection.send(
                "auth",
                {"type": "passcode", "passcode": self._password}
        )

        if not reply["data"]["success"]:
            self._set_connected_failed()

    async def connect(self) -> bool:
        """
        Attempt to connect to the room and start handling events.

        This function returns once the Room is fully connected, i. e.
        authenticated, using the correct nick and able to post messages.
        """

        if not await self._connection.connect():
            return False

        await self._connected.wait()
        if not self._connected_successfully:
            return False

        self._events.fire("connected")
        return True

    async def disconnect(self) -> None:
        """
        Disconnect from the room and stop the Room.

        This function has the potential to mess things up, and it has not yet
        been tested thoroughly. Use at your own risk, especially if you want to
        call connect() after calling disconnect().
        """

        self._set_connected_reset()
        await self._connection.disconnect()

    # Other events

    async def _on_disconnect_event(self, packet: Any) -> None:
        reason = packet["data"]["reason"]

        if reason == "authentication changed":
            await self._connection.reconnect()

        self._events.fire("disconnect", reason)

    async def _on_join_event(self, packet: Any) -> None:
        data = packet["data"]

        session = LiveSession.from_data(self, data)
        self._users = self.users.with_join(session)

        logger.info(f"&{self.name}: {session.atmention} joined")
        self._events.fire("join", session)

    async def _on_login_event(self, packet: Any) -> None:
        """
        Just reconnect, see
        https://github.com/euphoria-io/heim/blob/master/client/lib/stores/chat.js#L275-L276
        """

        data = packet["data"]

        account_id = data["account_id"]

        self._events.fire("login", account_id)
        logger.info(f"&{self.name}: Got logged in to {account_id}, reconnecting")

        await self._connection.reconnect()

    async def _on_logout_event(self, packet: Any) -> None:
        """
        Just reconnect, see
        https://github.com/euphoria-io/heim/blob/master/client/lib/stores/chat.js#L275-L276
        """

        self._events.fire("logout")
        logger.info(f"&{self.name}: Got logged out, reconnecting")

        await self._connection.reconnect()

    async def _on_network_event(self, packet: Any) -> None:
        data = packet["data"]

        if data["type"] == "partition":
            server_id = data["server_id"]
            server_era = data["server_era"]

            users = self.users

            for user in self.users:
                if user.server_id == server_id and user.server_era == server_era:
                    users = users.with_part(user)
                    logger.info(f"&{self.name}: {user.atmention} left")
                    self._events.fire("part", user)

            self._users = users

    async def _on_nick_event(self, packet: Any) -> None:
        data = packet["data"]
        session_id = data["session_id"]
        nick_from = data["from"]
        nick_to = data["to"]

        session = self.users.get(session_id)
        if session is not None:
            self._users = self.users.with_nick(session, nick_to)
        else:
            await self.who() # recalibrating self._users

        logger.info(f"&{self.name}: {atmention(nick_from)} is now called {atmention(nick_to)}")
        self._events.fire("nick", session, nick_from, nick_to)

    async def _on_edit_message_event(self, packet: Any) -> None:
        data = packet["data"]

        message = LiveMessage.from_data(self, data)

        self._events.fire("edit", message)

    async def _on_part_event(self, packet: Any) -> None:
        data = packet["data"]

        session = LiveSession.from_data(self, data)
        self._users = self.users.with_part(session)

        logger.info(f"&{self.name}: {session.atmention} left")
        self._events.fire("part", session)

    async def _on_pm_initiate_event(self, packet: Any) -> None:
        data = packet["data"]
        from_id = data["from"]
        from_nick = data["from_nick"]
        from_room = data["from_room"]
        pm_id = data["pm_id"]

        self._events.fire("pm", from_id, from_nick, from_room, pm_id)

    async def _on_send_event(self, packet: Any) -> None:
        data = packet["data"]

        message = LiveMessage.from_data(self, data)

        self._events.fire("send", message)

    # Attributes, ordered the same as in __init__

    def _wrap_optional(self, x: Optional[T]) -> T:
        if x is None:
            raise RoomNotConnectedException()

        return x

    @property
    def name(self) -> str:
        return self._name

    @property
    def password(self) -> Optional[str]:
        return self._password

    @property
    def target_nick(self) -> str:
        return self._target_nick

    @property
    def url_format(self) -> str:
        return self._url_format

    @property
    def session(self) -> LiveSession:
        return self._wrap_optional(self._session)

    @property
    def account(self) -> Account:
        return self._wrap_optional(self._account)

    @property
    def private(self) -> bool:
        return self._wrap_optional(self._private)

    @property
    def version(self) -> str:
        return self._wrap_optional(self._version)

    @property
    def users(self) -> LiveSessionListing:
        return self._wrap_optional(self._users)

    @property
    def pm_with_nick(self) -> str:
        return self._wrap_optional(self._pm_with_nick)

    @property
    def pm_with_user_id(self) -> str:
        return self._wrap_optional(self._pm_with_user_id)

    @property
    def url(self) -> str:
        return self._url

    # Functionality

    def _extract_data(self, packet: Any) -> Any:
        error = packet.get("error")
        if error is not None:
            raise EuphError(error)

        return packet["data"]

    async def _ensure_connected(self) -> None:
        await self._connected.wait()

        if not self._connected_successfully:
            raise RoomNotConnectedException()

    async def send(self,
            content: str,
            parent_id: Optional[str] = None
            ) -> LiveMessage:
        await self._ensure_connected()

        data = {"content": content}
        if parent_id is not None:
            data["parent"] = parent_id

        reply = await self._connection.send("send", data)
        data = self._extract_data(reply)

        return LiveMessage.from_data(self, data)

    async def _nick(self, nick: str) -> str:
        """
        This function implements all of the nick-setting logic except waiting
        for the room to actually connect. This is because connect() actually
        uses this function to set the desired nick before the room is
        connected.
        """

        logger.debug(f"Setting nick to {nick!r}")

        self._target_nick = nick

        reply = await self._connection.send("nick", {"name": nick})
        data = self._extract_data(reply)

        new_nick = data["to"]
        self._target_nick = new_nick

        if self._session is not None:
            self._session = self._session.with_nick(new_nick)

        logger.debug(f"Set nick to {new_nick!r}")

        return new_nick

    async def nick(self, nick: str) -> str:
        await self._ensure_connected()

        return await self._nick(nick)

    async def get(self, message_id: str) -> LiveMessage:
        await self._ensure_connected()

        reply = await self._connection.send("get-message", {"id": message_id})
        data = self._extract_data(reply)

        return LiveMessage.from_data(self, data)

    async def log(self,
            amount: int,
            before_id: Optional[str] = None
            ) -> List[LiveMessage]:
        await self._ensure_connected()

        data: Any = {"n": amount}
        if before_id is not None:
            data["before"] = before_id

        reply = await self._connection.send("log", data)
        data = self._extract_data(reply)

        messages = [LiveMessage.from_data(self, msg_data)
                for msg_data in data["log"]]
        return messages

    async def who(self) -> LiveSessionListing:
        await self._ensure_connected()

        reply = await self._connection.send("who", {})
        data = self._extract_data(reply)

        users = LiveSessionListing.from_data(self, data["listing"])
        # Assumes that self._session is set (we're connected)
        session = users.get(self.session.session_id)
        if session is not None:
            self._session = session
            self._users = users.with_part(self._session)
        else:
            self._users = users

        return self._users

    async def login(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Since euphoria appears to only support email authentication, this way
        of logging in is hardcoded here.

        Returns whether the login was successful. If it was, the second
        parameter is the account id. If it wasn't, the second parameter is the
        reason why the login failed.
        """

        data: Any = {
                "namespace": "email",
                "id": email,
                "password": password,
        }

        reply = await self._connection.send("login", data)
        data = self._extract_data(reply)

        success: bool = data["success"]
        account_id_or_reason = data.get("account_id") or data["reason"]

        if success:
            logger.info(f"&{self.name}: Logged in as {account_id_or_reason}")
        else:
            logger.info(f"&{self.name}: Failed to log in with {email} because {account_id_or_reason}")

        await self._connection.reconnect()

        return success, account_id_or_reason

    async def logout(self) -> None:
        await self._connection.send("logout", {})

        logger.info(f"&{self.name}: Logged out")

        await self._connection.reconnect()

    async def pm(self, user_id: str) -> Tuple[str, str]:
        """
        Returns the pm_id of the pm and the nick of the person being pinged.
        """

        data = {"user_id": user_id}

        reply = await self._connection.send("pm-initiate", data)
        data = self._extract_data(reply)

        pm_id = data["pm_id"]
        to_nick = data["to_nick"]
        return pm_id, to_nick
