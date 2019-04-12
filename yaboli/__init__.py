import asyncio
import logging
from typing import Callable

from .bot import *
from .client import *
from .command import *
from .connection import *
from .events import *
from .exceptions import *
from .message import *
from .module import *
from .room import *
from .session import *
from .util import *

__all__ = ["STYLE", "FORMAT", "DATE_FORMAT", "FORMATTER", "enable_logging",
        "run"]

__all__ += bot.__all__
__all__ += client.__all__
__all__ += command.__all__
__all__ += connection.__all__
__all__ += events.__all__
__all__ += exceptions.__all__
__all__ += message.__all__
__all__ += module.__all__
__all__ += room.__all__
__all__ += session.__all__
__all__ += util.__all__

STYLE = "{"
FORMAT = "{asctime} [{levelname:<7}] <{name}>: {message}"
DATE_FORMAT = "%F %T"

FORMATTER = logging.Formatter(
        fmt=FORMAT,
        datefmt=DATE_FORMAT,
        style=STYLE
)

def enable_logging(name: str = "yaboli", level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(FORMATTER)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

def run(
        client: Callable[[str], Client],
        config_file: str = "bot.conf"
        ) -> None:
    async def _run():
        client_ = client(config_file)
        await client_.run()

    asyncio.run(_run())
