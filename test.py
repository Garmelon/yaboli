# These tests are not intended as serious tests, just as small scenarios to
# give yaboli something to do.

import asyncio
import logging

import yaboli

FORMAT = "{asctime} [{levelname:<7}] <{name}> {funcName}(): {message}"
LEVEL = logging.DEBUG
#FORMAT = "{asctime} [{levelname:<7}] <{name}>: {message}"
#LEVEL = logging.INFO

DATE_FORMAT = "%F %T"
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    fmt=FORMAT,
    datefmt=DATE_FORMAT,
    style="{"
))

logger = logging.getLogger('yaboli')
logger.setLevel(LEVEL)
logger.addHandler(handler)

class TestModule(yaboli.Module):
    PING_REPLY = "ModulePong!"
    DESCRIPTION = "ModuleDescription"
    HELP_GENERAL = "ModuleGeneralHelp"
    HELP_SPECIFIC = ["ModuleGeneralHelp"]

class EchoModule(yaboli.Module):
    DEFAULT_NICK = "echo"
    DESCRIPTION = "echoes back the input arguments"
    HELP_GENERAL = "/me " + DESCRIPTION
    HELP_SPECIFIC = [
            "!echo <args> – output the arguments, each in its own line"
            #"!fancyecho <args> – same as !echo, but different parser"
    ]

    def __init__(self, standalone: bool) -> None:
        super().__init__(standalone)

        self.register_general("echo", self.cmd_echo)
        #self.register_general("fancyecho", self.cmd_fancyecho)

    async def cmd_echo(self, room, message, args):
        if args.has_args():
            lines = [repr(arg) for arg in args.basic()]
            await message.reply("\n".join(lines))
        else:
            await message.reply("No arguments")

class TestBot(yaboli.ModuleBot):
    DEFAULT_NICK = "testbot"

    async def started(self):
        await self.join("test")

async def main():
    tb = TestBot()
    tb.register_module("test", TestModule(standalone=False))
    tb.register_module("echo", EchoModule(standalone=False))
    await tb.run()

asyncio.run(main())
