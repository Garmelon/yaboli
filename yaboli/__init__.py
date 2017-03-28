import logging
logging.basicConfig(
	level=logging.DEBUG,
	format="[{levelname: <7}] in {threadName: <17} <{name}>: {message}",
	style="{"
)

from .basic_types import Message, SessionView
from .callbacks import Callbacks
from .connection import Connection
from .session import Session
