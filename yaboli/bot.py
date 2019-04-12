import datetime
import logging
from typing import List, Optional

from .client import Client
from .command import *
from .message import LiveMessage, Message
from .room import Room
from .util import *

logger = logging.getLogger(__name__)

__all__ = ["Bot"]

class Bot(Client):
    PING_REPLY: str = "Pong!"
    HELP_GENERAL: Optional[str] = None
    HELP_SPECIFIC: Optional[List[str]] = None

    def __init__(self) -> None:
        super().__init__()

        self._commands: List[Command] = []

        self.start_time = datetime.datetime.now()

    # Registering commands

    def register(self, command: Command) -> None:
        self._commands.append(command)

    def register_general(self,
            name: str,
            cmdfunc: GeneralCommandFunction,
            args: bool = True
            ) -> None:
        command = GeneralCommand(name, cmdfunc, args)
        self.register(command)

    def register_specific(self,
            name: str,
            cmdfunc: SpecificCommandFunction,
            args: bool = True
            ) -> None:
        command = SpecificCommand(name, cmdfunc, args)
        self.register(command)

    # Processing commands

    async def process_commands(self,
            room: Room,
            message: LiveMessage,
            aliases: List[str] = []
            ) -> None:
        nicks = [room.session.nick] + aliases
        data = CommandData.from_string(message.content)

        if data is not None:
            logger.debug(f"Processing command from {message.content!r}")
            for command in self._commands:
                await command.run(room, message, nicks, data)

    async def on_send(self, room: Room, message: LiveMessage) -> None:
        await self.process_commands(room, message)

    # Help util

    def format_help(self, room: Room, lines: List[str]) -> str:
        text = "\n".join(lines)
        params = {
                "nick": room.session.nick,
                "mention": room.session.mention,
                "atmention": room.session.atmention,
        }
        return text.format(**params)

    # Botrulez

    def register_botrulez(self,
            ping: bool = True,
            help_: bool = True,
            uptime: bool = True
            ) -> None:
        if ping:
            self.register_general("ping", self.cmd_ping, args=False)
            self.register_specific("ping", self.cmd_ping, args=False)

        if help_:
            if self.HELP_GENERAL is None and self.HELP_SPECIFIC is None:
                logger.warn(("HELP_GENERAL and HELP_SPECIFIC are None, but the"
                    " help command is enabled"))
            self.register_general("help", self.cmd_help_general, args=False)
            self.register_specific("help", self.cmd_help_specific, args=False)

        if uptime:
            self.register_specific("uptime", self.cmd_uptime, args=False)

    async def cmd_ping(self,
            room: Room,
            message: LiveMessage,
            args: ArgumentData
            ) -> None:
        await message.reply(self.PING_REPLY)

    async def cmd_help_general(self,
            room: Room,
            message: LiveMessage,
            args: ArgumentData
            ) -> None:
        if self.HELP_GENERAL is not None:
            await message.reply(self.format_help(room, [self.HELP_GENERAL]))

    async def cmd_help_specific(self,
            room: Room,
            message: LiveMessage,
            args: SpecificArgumentData
            ) -> None:
        if self.HELP_SPECIFIC is not None:
            await message.reply(self.format_help(room, self.HELP_SPECIFIC))

    async def cmd_uptime(self,
            room: Room,
            message: LiveMessage,
            args: SpecificArgumentData
            ) -> None:
        time = format_time(self.start_time)
        delta = format_delta(datetime.datetime.now() - self.start_time)
        text = f"/me has been up since {time} UTC ({delta})"
        await message.reply(text)
