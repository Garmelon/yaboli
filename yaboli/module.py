import configparser
import logging
from typing import Callable, Dict, List, Optional

from .bot import Bot
from .command import *
from .message import LiveMessage
from .room import Room
from .session import LiveSession
from .util import *

logger = logging.getLogger(__name__)

__all__ = ["Module", "ModuleConstructor", "ModuleBot", "ModuleBotConstructor"]

class Module(Bot):
    DESCRIPTION: Optional[str] = None

    def __init__(self,
            config: configparser.ConfigParser,
            config_file: str,
            standalone: bool = True,
            ) -> None:
        super().__init__(config, config_file)

        self.standalone = standalone

ModuleConstructor = Callable[[configparser.ConfigParser, str, bool], Module]

class ModuleBot(Bot):
    HELP_PRE: Optional[List[str]] = [
            "This bot contains the following modules:"
    ]
    HELP_POST: Optional[List[str]] = [
            "",
            "For module-specific help, try \"!help {atmention} <module>\".",
    ]
    MODULE_HELP_LIMIT = 5

    MODULES_SECTION = "modules"

    def __init__(self,
            config: configparser.ConfigParser,
            config_file: str,
            module_constructors: Dict[str, ModuleConstructor],
            ) -> None:
        super().__init__(config, config_file)

        self.module_constructors = module_constructors
        self.modules: Dict[str, Module] = {}

        # Load initial modules
        for module_name in self.config[self.MODULES_SECTION]:
            module_constructor = self.module_constructors.get(module_name)
            if module_constructor is None:
                logger.warn(f"Module {module_name} not found")
                continue
            # standalone is set to False
            module = module_constructor(self.config, self.config_file, False)
            self.load_module(module_name, module)

    def load_module(self, name: str, module: Module) -> None:
        if name in self.modules:
            logger.warn(f"Module {name!r} is already registered, overwriting...")
        self.modules[name] = module

    def unload_module(self, name: str) -> None:
        if name in self.modules:
            del self.modules[name]

    # Better help messages

    def compile_module_overview(self) -> List[str]:
        lines = []

        if self.HELP_PRE is not None:
            lines.extend(self.HELP_PRE)

        any_modules = False

        modules_without_desc: List[str] = []
        for module_name in sorted(self.modules):
            any_modules = True

            module = self.modules[module_name]

            if module.DESCRIPTION is None:
                modules_without_desc.append(module_name)
            else:
                line = f"\t{module_name} — {module.DESCRIPTION}"
                lines.append(line)

        if modules_without_desc:
            lines.append("\t" + ", ".join(modules_without_desc))

        if not any_modules:
            lines.append("No modules loaded.")

        if self.HELP_POST is not None:
            lines.extend(self.HELP_POST)

        return lines

    def compile_module_help(self, module_name: str) -> List[str]:
        module = self.modules.get(module_name)
        if module is None:
            return [f"Module {module_name!r} not found."]

        elif module.HELP_SPECIFIC is None:
            return [f"Module {module_name!r} has no detailed help message."]

        return module.HELP_SPECIFIC

    async def cmd_modules_help(self,
            room: Room,
            message: LiveMessage,
            args: SpecificArgumentData
            ) -> None:
        if args.has_args():
            if len(args.basic()) > self.MODULE_HELP_LIMIT:
                limit = self.MODULE_HELP_LIMIT
                text = f"A maximum of {limit} module{plural(limit)} is allowed."
                await message.reply(text)
            else:
                for module_name in args.basic():
                    help_lines = self.compile_module_help(module_name)
                    await message.reply(self.format_help(room, help_lines))
        else:
            help_lines = self.compile_module_overview()
            await message.reply(self.format_help(room, help_lines))

    # Sending along all kinds of events

    async def on_connected(self, room: Room) -> None:
        await super().on_connected(room)

        for module in self.modules.values():
            await module.on_connected(room)

    async def on_snapshot(self, room: Room, messages: List[LiveMessage]) -> None:
        await super().on_snapshot(room, messages)

        for module in self.modules.values():
            await module.on_snapshot(room, messages)

    async def on_send(self, room: Room, message: LiveMessage) -> None:
        await super().on_send(room, message)

        for module in self.modules.values():
            await module.on_send(room, message)

    async def on_join(self, room: Room, user: LiveSession) -> None:
        await super().on_join(room, user)

        for module in self.modules.values():
            await module.on_join(room, user)

    async def on_part(self, room: Room, user: LiveSession) -> None:
        await super().on_part(room, user)

        for module in self.modules.values():
            await module.on_part(room, user)

    async def on_nick(self,
            room: Room,
            user: LiveSession,
            from_nick: str,
            to_nick: str
            ) -> None:
        await super().on_nick(room, user, from_nick, to_nick)

        for module in self.modules.values():
            await module.on_nick(room, user, from_nick, to_nick)

    async def on_edit(self, room: Room, message: LiveMessage) -> None:
        await super().on_edit(room, message)

        for module in self.modules.values():
            await module.on_edit(room, message)

    async def on_login(self, room: Room, account_id: str) -> None:
        await super().on_login(room, account_id)

        for module in self.modules.values():
            await module.on_login(room, account_id)

    async def on_logout(self, room: Room) -> None:
        await super().on_logout(room)

        for module in self.modules.values():
            await module.on_logout(room)

    async def on_pm(self,
            room: Room,
            from_id: str,
            from_nick: str,
            from_room: str,
            pm_id: str
            ) -> None:
        await super().on_pm(room, from_id, from_nick, from_room, pm_id)

        for module in self.modules.values():
            await module.on_pm(room, from_id, from_nick, from_room, pm_id)

    async def on_disconnect(self, room: Room, reason: str) -> None:
        await super().on_disconnect(room, reason)

        for module in self.modules.values():
            await module.on_disconnect(room, reason)

ModuleBotConstructor = Callable[
        [configparser.ConfigParser, str, Dict[str, ModuleConstructor]],
        Bot
]
