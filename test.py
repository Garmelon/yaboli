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
        self.stop = asyncio.Event()

    async def run(self):
        await self.room.connect()
        await self.stop.wait()

async def main():
    tc = TestClient()
    await tc.run()

asyncio.run(main())
