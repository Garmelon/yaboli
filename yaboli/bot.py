import configparser
import datetime
import logging
from typing import Callable, List, Optional

from .client import Client
from .command import *
from .message import LiveMessage, Message
from .room import Room
from .util import *

logger = logging.getLogger(__name__)

__all__ = ["Bot", "BotConstructor"]

class Bot(Client):
    """
    A Bot is a Client that responds to commands and uses a config file to
    automatically set its nick and join rooms.

    The config file is loaded as a ConfigParser by the run() or run_modulebot()
    functions and has the following structure:

    A "general" section which contains:
    - nick - the default nick of the bot (set to the empty string if you don't
      want to set a nick)
    - cookie_file (optional) - the file the cookie should be saved in

    A "rooms" section which contains a list of rooms that the bot should
    automatically join. This section is optional if you overwrite started().
    The room list should have the format "roomname" or "roomname = password".

    A bot has the following attributes:
    - ALIASES - list of alternate nicks the bot responds to (see
      process_commands())
    - PING_REPLY - used by cmd_ping()
    - HELP_GENERAL - used by cmd_help_general()
    - HELP_SPECIFIC - used by cmd_help_specific()
    - KILL_REPLY - used by cmd_kill()
    - RESTART_REPLY - used by cmd_restart()
    - GENERAL_SECTION - the name of the "general" section in the config file
      (see above) (default: "general")
    - ROOMS_SECTION - the name of the "rooms" section in the config file (see
      above) (default: "rooms")
    """

    ALIASES: List[str] = []

    PING_REPLY: str = "Pong!"
    HELP_GENERAL: Optional[str] = None
    HELP_SPECIFIC: Optional[List[str]] = None
    KILL_REPLY: Optional[str] = "/me dies"
    RESTART_REPLY: Optional[str] = "/me restarts"

    GENERAL_SECTION = "general"
    ROOMS_SECTION = "rooms"

    def __init__(self,
            config: configparser.ConfigParser,
            config_file: str,
            ) -> None:
        self.config = config
        self.config_file = config_file

        nick = self.config[self.GENERAL_SECTION].get("nick")
        if nick is None:
            logger.warn(("'nick' not set in config file. Defaulting to empty"
                    " nick"))
            nick = ""

        cookie_file = self.config[self.GENERAL_SECTION].get("cookie_file")
        if cookie_file is None:
            logger.warn(("'cookie_file' not set in config file. Using no cookie"
                    " file."))

        super().__init__(nick, cookie_file=cookie_file)

        self._commands: List[Command] = []

        self.start_time = datetime.datetime.now()

    def save_config(self) -> None:
        """
        Save the current state of self.config to the file passed in __init__ as
        the config_file parameter.

        Usually, this is the file that self.config was loaded from (if you use
        run or run_modulebot).
        """

        with open(self.config_file, "w") as f:
            self.config.write(f)

    async def started(self) -> None:
        """
        This Client function is overwritten in order to join all the rooms
        listed in the "rooms" section of self.config.

        If you need to overwrite this function but want to keep the auto-join
        functionality, make sure to await super().started().
        """

        for room, password in self.config[self.ROOMS_SECTION].items():
            if password is None:
                await self.join(room)
            else:
                await self.join(room, password=password)

    # Registering commands

    def register(self, command: Command) -> None:
        """
        Register a Command (from the yaboli.command submodule).

        Usually, you don't have to call this function yourself.
        """

        self._commands.append(command)

    def register_general(self,
            name: str,
            cmdfunc: GeneralCommandFunction,
            args: bool = True
            ) -> None:
        """
        Register a function as general bot command (i. e. no @mention of the
        bot nick after the !command). This function will be called by
        process_commands() when the bot encounters a matching command.

        name - the name of the command (If you want your command to be !hello,
        the name is "hello".)

        cmdfunc - the function that is called with the Room, LiveMessage and
        ArgumentData when the bot encounters a matching command

        args - whether the command may have arguments (If set to False, the
        ArgumentData's has_args() function must also return False for the
        command function to be called. If set to True, all ArgumentData is
        valid.)
        """

        command = GeneralCommand(name, cmdfunc, args)
        self.register(command)

    def register_specific(self,
            name: str,
            cmdfunc: SpecificCommandFunction,
            args: bool = True
            ) -> None:
        """
        Register a function as specific bot command (i. e. @mention of the bot
        nick after the !command is required). This function will be called by
        process_commands() when the bot encounters a matching command.

        name - the name of the command (see register_general() for an
        explanation)

        cmdfunc - the function that is called with the Room, LiveMessage and
        SpecificArgumentData when the bot encounters a matching command

        args - whether the command may have arguments (see register_general()
        for an explanation)
        """

        command = SpecificCommand(name, cmdfunc, args)
        self.register(command)

    # Processing commands

    async def process_commands(self,
            room: Room,
            message: LiveMessage,
            aliases: List[str] = []
            ) -> None:
        """
        If the message contains a command, call all matching command functions
        that were previously registered.

        This function is usually called by the overwritten on_send() function.
        """

        nicks = [room.session.nick] + aliases
        data = CommandData.from_string(message.content)

        if data is not None:
            logger.debug(f"Processing command from {message.content!r}")
            for command in self._commands:
                await command.run(room, message, nicks, data)

    async def on_send(self, room: Room, message: LiveMessage) -> None:
        """
        This Client function is overwritten in order to automatically call
        process_commands() with self.ALIASES.

        If you need to overwrite this function, make sure to await
        process_commands() with self.ALIASES somewhere in your function, or
        await super().on_send().
        """

        await self.process_commands(room, message, aliases=self.ALIASES)

    # Help util

    def format_help(self, room: Room, lines: List[str]) -> str:
        """
        Format a list of strings into a string, replacing certain placeholders
        with the actual values.

        This function uses the str.format() function to replace the following:

        - {nick} - the bot's current nick
        - {mention} - the bot's current nick, run through mention()
        - {atmention} - the bot's current nick, run through atmention()
        """

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
            uptime: bool = True,
            kill: bool = False,
            restart: bool = False,
            ) -> None:
        """
        Register the commands necessary for the bot to conform to the botrulez
        (https://github.com/jedevc/botrulez). Also includes a few optional
        botrulez commands that are disabled by default.

        - ping - register general and specific cmd_ping()
        - help_ - register cmd_help_general() and cmd_help_specific()
        - uptime - register specific cmd_uptime
        - kill - register specific cmd_kill (disabled by default)
        - uptime - register specific cmd_uptime (disabled by default)

        All commands are registered with args=False.

        If you want to implement your own versions of these commands, it is
        recommended that you set the respective argument to False in your call
        to register_botrulez(), overwrite the existing command functions or
        create your own, and then register them manually.

        For help, that might look something like this, if you've written a
        custom specific help that takes extra arguments but are using the
        botrulez general help:

        self.register_botrulez(help_=False)
        self.register_general("help", self.cmd_help_general, args=False)
        self.register_specific("help", self.cmd_help_custom)

        In case you're asking, the help_ parameter has an underscore at the end
        so it doesn't overlap the help() function.
        """

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

        if kill:
            self.register_specific("kill", self.cmd_kill, args=False)

        if restart:
            self.register_specific("restart", self.cmd_restart, args=False)

    async def cmd_ping(self,
            room: Room,
            message: LiveMessage,
            args: ArgumentData
            ) -> None:
        """
        Reply with self.PING_REPLY.
        """

        await message.reply(self.PING_REPLY)

    async def cmd_help_general(self,
            room: Room,
            message: LiveMessage,
            args: ArgumentData
            ) -> None:
        """
        Reply with self.HELP_GENERAL, if it is not None. Uses format_help().
        """

        if self.HELP_GENERAL is not None:
            await message.reply(self.format_help(room, [self.HELP_GENERAL]))

    async def cmd_help_specific(self,
            room: Room,
            message: LiveMessage,
            args: SpecificArgumentData
            ) -> None:
        """
        Reply with self.HELP_SPECIFIC, if it is not None. Uses format_help().
        """

        if self.HELP_SPECIFIC is not None:
            await message.reply(self.format_help(room, self.HELP_SPECIFIC))

    async def cmd_uptime(self,
            room: Room,
            message: LiveMessage,
            args: SpecificArgumentData
            ) -> None:
        """
        Reply with the bot's uptime in the format specified by the botrulez.

        This uses the time that the Bot was first started, not the time the
        respective Room was created. A !restart (see register_botrulez()) will
        reset the bot uptime, but leaving and re-joining a room or losing
        connection won't.
        """

        time = format_time(self.start_time)
        delta = format_delta(datetime.datetime.now() - self.start_time)
        text = f"/me has been up since {time} UTC ({delta})"
        await message.reply(text)

    async def cmd_kill(self,
            room: Room,
            message: LiveMessage,
            args: SpecificArgumentData
            ) -> None:
        """
        Remove the bot from this room.

        If self.KILL_REPLY is not None, replies with that before leaving the
        room.
        """

        logger.info(f"Killed in &{room.name} by {message.sender.atmention}")

        if self.KILL_REPLY is not None:
            await message.reply(self.KILL_REPLY)

        await self.part(room)

    async def cmd_restart(self,
            room: Room,
            message: LiveMessage,
            args: SpecificArgumentData
            ) -> None:
        """
        Restart the whole Bot.

        This is done by stopping the Bot, since the run() or run_modulebot()
        functions start the Bot in a while True loop.

        If self.RESTART_REPLY is not None, replies with that before restarting.
        """

        logger.info(f"Restarted in &{room.name} by {message.sender.atmention}")

        if self.RESTART_REPLY is not None:
            await message.reply(self.RESTART_REPLY)

        await self.stop()

BotConstructor = Callable[[configparser.ConfigParser, str], Bot]
