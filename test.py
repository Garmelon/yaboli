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

class TestBot(yaboli.Bot):
    DEFAULT_NICK = "testbot"

    def __init__(self):
        super().__init__()
        self.register_botrulez()
        self.register_general("test", self.cmd_test, args=False)
        self.register_general("who", self.cmd_who, args=False)
        self.register_general("err", self.cmd_err, args=False)

    async def started(self):
        await self.join("test")

    async def on_send(self, room, message):
        await self.process_commands(room, message,
                aliases=["testalias", "aliastest"])

    async def cmd_test(self, room, message, args):
        await message.reply(f"You said {message.content!r}.")
        msg1 = await room.send(f"{message.sender.atmention} said something.")
        await msg1.reply("Yes, they really did.")

    async def cmd_who(self, room, message, args):
        lines = []
        for user in await room.who():
            lines.append(repr(user.nick))
        await message.reply("\n".join(lines))

    async def cmd_err(self, room, message, args):
        await message.reply(str(1/0))

async def main():
    tc = TestBot()
    await tc.run()

asyncio.run(main())
