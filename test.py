# These tests are not intended as serious tests, just as small scenarios to
# give yaboli something to do.

import asyncio
import logging

from yaboli import Room

FORMAT = "{asctime} [{levelname:<7}] <{name}> {funcName}(): {message}"
DATE_FORMAT = "%F %T"
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    fmt=FORMAT,
    datefmt=DATE_FORMAT,
    style="{"
))

logger = logging.getLogger('yaboli')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

class TestClient:
    def __init__(self):
        self.room = Room("test", target_nick="testbot")
        self.room.register_event("join", self.on_join)
        self.room.register_event("part", self.on_part)
        self.room.register_event("send", self.on_send)

        self.stop = asyncio.Event()

    async def run(self):
        await self.room.connect()
        await self.stop.wait()

    async def on_join(self, user):
        print()
        print(f"{user.nick} ({user.atmention}) joined.")
        if user.is_person:
            print("They're a person!")
        elif user.is_bot:
            print("They're just a bot")
        else:
            print("This should never happen")
        print()

    async def on_part(self, user):
        print(f"{user.nick} left")

    async def on_send(self, message):
        await message.reply(f"You said {message.content!r}.")
        msg1 = await message.room.send(f"{message.sender.atmention} said something.")
        await msg1.reply("Yes, they really did.")

async def main():
    tc = TestClient()
    await tc.run()

asyncio.run(main())
