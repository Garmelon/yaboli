import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s|%(name)s|%(levelname)s| %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
logger.addHandler(sh)

from .bot import Bot
from .botmanager import BotManager
from .callbacks import Callbacks
from .exceptions import YaboliException, CreateBotException
from .mention import Mention
