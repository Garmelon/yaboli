import json

from . import bot
from . import exceptions

class BotManager():
	"""
	Keep track of multiple bots in different rooms.
	"""
	
	def __init__(self, bot_class, default_nick="yaboli", max_bots=100,
	             bots_file="bots.json", data_file="data.json"):
		"""
		bot_class    - class to create instances of
		default_nick - default nick for all bots to assume when no nick is specified
		max_bots     - maximum number of bots allowed to exist simultaneously
		               None or 0 - no limit
		bots_file    - file the bot backups are saved to
		               None - no bot backups
		data_file    - file the bot data is saved to
		             - None - bot data isn't saved
		"""
		
		self.bot_class = bot_class
		self.max_bots = max_bots
		self.default_nick = default_nick
		
		self.bots_file = bots_file
		self.data_file = data_file
		
		self._bots = {}
		self._bot_id = 0
		self._bot_data = {}
		
		self._load_bots()
	
	def create(self, room, password=None, nick=None):
		"""
		create(room, password, nick) -> bot
		
		Create a new bot in room.
		"""
		
		if nick is None:
			nick = self.default_nick
		
		if self.max_bots and len(self._bots) >= self.max_bots:
			raise exceptions.CreateBotException("max_bots limit hit")
		else:
			bot = self.bot_class(room, nick=nick, password=password, manager=self)
			self._bots[self._bot_id] = bot
			self._bot_id += 1
			
			self._save_bots()
			
			return bot
	
	def remove(self, bot_id):
		"""
		remove(bot_id) -> None
		
		Kill a bot and remove it from the list of bots.
		"""
		
		if bot_id in self._bots:
			self._bots[bot_id].stop()
			self._bots.pop(bot_id)
			
			self._save_bots()
	
	def get(self, bot_id):
		"""
		get(self, bot_id) -> bot
		
		Return bot with that id, if found.
		"""
		
		if bot_id in self._bots:
			return self._bots[bot_id]
	
	def get_id(self, bot):
		"""
		get_id(bot) -> bot_id
		
		Return the bot id, if the bot is known.
		"""
		
		for bot_id, own_bot in self._bots.items():
			if bot == own_bot:
				return bot_id
	
	def get_similar(self, room, nick):
		"""
		get_by_room(room, nick) -> dict
		
		Collect all bots that are connected to the room and have that nick.
		"""
		
		return {bot_id: bot for bot_id, bot in self._bots.items()
		        if bot.roomname() == room and bot.mentionable().lower() == nick.lower()}
	
	def _load_bots(self):
		"""
		_load_bots() -> None
		
		Load and create bots from self.bots_file.
		"""
		
		if not self.bots_file:
			return
		
		try:
			with open(self.bots_file) as f:
				bots = json.load(f)
		except FileNotFoundError:
			pass
		else:
			for bot_info in bots:
				bot = self.create(bot_info["room"], password=bot_info["password"],
				                  nick=bot_info["nick"])
				bot.created_in = bot_info["created_in"]
				bot.created_by = bot_info["created_by"]
	
	def _save_bots(self):
		"""
		_save_bots() -> None
		
		Save all current bots to self.bots_file.
		"""
		
		if not self.bots_file:
			return
		
		bots = []
		
		for bot_id, bot in self._bots.items():
			bot_info = {}
			
			bot_info["room"]       = bot.roomname()
			bot_info["password"]   = bot.password()
			bot_info["nick"]       = bot.nick()
			bot_info["created_in"] = bot.created_in
			bot_info["created_by"] = bot.created_by
			
			bots.append(bot_info)
		
		with open(self.bots_file, "w") as f:
			json.dump(bots, f)
