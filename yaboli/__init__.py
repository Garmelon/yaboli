import asyncio
#asyncio.get_event_loop().set_debug(True) # uncomment for asycio debugging mode

import logging

# general (asyncio) logging level
#logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.WARNING)

# yaboli logger level
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

from .bot import *
from .connection import *
from .controller import *
from .database import *
from .room import *
from .utils import *

__all__ = (
	bot.__all__ +
	connection.__all__ +
	controller.__all__ +
	database.__all__ +
	room.__all__ +
	utils.__all__
)
