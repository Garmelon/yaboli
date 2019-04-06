# These tests are not intended as serious tests, just as small scenarios to
# give yaboli something to do.

import asyncio
import logging

from yaboli import Connection

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

async def main():
    conn = Connection("wss://echo.websocket.org")

    print()
    print("  DISCONNECTING TWICE AT THE SAME TIME")
    print("Connected successfully:", await conn.connect())
    a = asyncio.create_task(conn.disconnect())
    b = asyncio.create_task(conn.disconnect())
    await a
    await b

    print()
    print("  DISCONNECTING WHILE CONNECTING (test not working properly)")
    asyncio.create_task(conn.disconnect())
    await asyncio.sleep(0)
    print("Connected successfully:", await conn.connect())
    await conn.disconnect()

    print()
    print("  WAITING FOR PING TIMEOUT")
    print("Connected successfully:", await conn.connect())
    await asyncio.sleep(conn.PING_TIMEOUT + 10)
    await conn.disconnect()

asyncio.run(main())
