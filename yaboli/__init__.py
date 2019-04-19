import asyncio
import configparser
import logging
from typing import Callable, Dict

from .bot import *
from .client import *
from .command import *
from .connection import *
from .database import *
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
__all__ += database.__all__
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
        bot_constructor: BotConstructor,
        config_file: str = "bot.conf",
        ) -> None:
    async def _run() -> None:
        while True:
            # Load the config file
            config = configparser.ConfigParser(allow_no_value=True)
            config.read(config_file)

            bot = bot_constructor(config, config_file)
            await bot.run()

    asyncio.run(_run())

def run_modulebot(
        modulebot_constructor: ModuleBotConstructor,
        module_constructors: Dict[str, ModuleConstructor],
        config_file: str = "bot.conf",
        ) -> None:
    async def _run() -> None:
        while True:
            # Load the config file
            config = configparser.ConfigParser(allow_no_value=True)
            config.read(config_file)

            modulebot = modulebot_constructor(config, config_file,
                    module_constructors)
            await modulebot.run()

    asyncio.run(_run())
