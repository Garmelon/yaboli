import logging
from typing import Dict, List, Optional

from .bot import Bot
from .command import *
from .message import LiveMessage
from .room import Room
from .session import LiveSession
from .util import *

logger = logging.getLogger(__name__)

__all__ = ["Module", "ModuleBot"]

class Module(Bot):
    DESCRIPTION: Optional[str] = None

    def __init__(self, config_file: str, standalone: bool) -> None:
        super().__init__(config_file)

        self.standalone = standalone

class ModuleBot(Bot):
    HELP_PRE: Optional[List[str]] = [
            "This bot contains the following modules:"
    ]
    HELP_POST: Optional[List[str]] = [
            ""
            "Use \"!help {atmention} <module>\" to get more information on a"
            " specific module."
    ]
    MODULE_HELP_LIMIT = 5

    def __init__(self, config_file: str) -> None:
        super().__init__(config_file)

        self.modules: Dict[str, Module] = {}

        self.register_botrulez(help_=False)
        self.register_general("help", self.cmd_help_general, args=False)
        self.register_specific("help", self.cmd_help_specific, args=True)

    def register_module(self, name: str, module: Module) -> None:
        if name in self.modules:
            logger.warn(f"Module {name!r} is already registered, overwriting...")
        self.modules[name] = module

    def compile_module_overview(self) -> List[str]:
        lines = []

        if self.HELP_PRE is not None:
            lines.extend(self.HELP_PRE)

        modules_without_desc: List[str] = []
        for module_name in sorted(self.modules):
            module = self.modules[module_name]

            if module.DESCRIPTION is None:
                modules_without_desc.append(module_name)
            else:
                line = f"\t{module_name} — {module.DESCRIPTION}"
                lines.append(line)

        if modules_without_desc:
            lines.append(", ".join(modules_without_desc))

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

    # Overwriting the botrulez help function
    async def cmd_help_specific(self,
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
