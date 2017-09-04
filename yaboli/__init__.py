import logging
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from .bot import *
from .connection import *
from .controller import *
from .room import *
from .utils import *

__all__ = connection.__all__ + room.__all__ + controller.__all__ + utils.__all__
