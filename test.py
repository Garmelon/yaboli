# These tests are not intended as serious tests, just as small scenarios to
# give yaboli something to do.

import asyncio
import logging

import yaboli

#FORMAT = "{asctime} [{levelname:<7}] <{name}> {funcName}(): {message}"
#LEVEL = logging.DEBUG
FORMAT = "{asctime} [{levelname:<7}] <{name}>: {message}"
LEVEL = logging.INFO

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

class TestClient(yaboli.Client):
    DEFAULT_NICK = "testbot"

    async def started(self):
        await self.join("test")

    async def on_send(self, room, message):
        if message.content == "!test":
            await message.reply(f"You said {message.content!r}.")
            msg1 = await room.send(f"{message.sender.atmention} said something.")
            await msg1.reply("Yes, they really did.")

async def main():
    tc = TestClient()
    await tc.run()

asyncio.run(main())
