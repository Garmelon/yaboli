import logging
logging.basicConfig(
	level=logging.DEBUG,
	format="[{levelname: <5}] in {threadName: <13} <{name}>: {message}",
	style="{"
)

from .basic_types import Message, SessionView
from .callbacks import Callbacks
from .connection import Connection
