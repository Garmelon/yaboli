from . import bot
from . import exceptions

class BotManager():
	"""
	Keep track of multiple bots in different rooms.
	"""
	
	def __init__(self, bot_class, default_nick="yaboli", max_bots=100):
		"""
		bot_class    - class to create instances of
		default_nick - default nick for all bots to assume when no nick is specified
		max_bots     - maximum number of bots allowed to exist simultaneously
		               None or 0 - no limit
		"""
		
		self.bot_class = bot_class
		self.max_bots = max_bots
		self.default_nick = default_nick
		
		self.bots = {}
		self.bot_id = 0
	
	def create(self, room, password=None, nick=None):
		"""
		create(room, password, nick) -> bot
		
		Create a new bot in room.
		"""
		
		if nick is None:
			nick = self.default_nick
		
		if self.max_bots and len(self.bots) >= self.max_bots:
			raise exceptions.CreateBotException("max_bots limit hit")
		else:
			bot = self.bot_class(room, nick=nick, password=password, manager=self)
			self.bots[self.bot_id] = bot
			self.bot_id += 1
			
			return bot
	
	def remove(self, bot_id):
		"""
		remove(bot_id) -> None
		
		Kill a bot and remove it from the list of bots.
		"""
		
		if not bot_id in self.bots:
			raise exceptions.BotNotFoundException("Bot not in bots list")
		
		self.bots[bot_id].stop()
		del self.bots[bot_id]
	
	def get(self, bot_id):
		"""
		get(self, bot_id) -> bot
		
		Return bot with that id, if found.
		"""
		
		if bot_id in self.bots:
			return self.bots[bot_id]
	
	def get_id(self, bot):
		"""
		get_id(bot) -> bot_id
		
		Return the bot id, if the bot is known.
		"""
		
		for bot_id, own_bot in self.bots.items():
			if bot == own_bot:
				return bot_id
	
	def get_similar(self, room, nick):
		"""
		get_by_room(room, nick) -> dict
		
		Collect all bots that are connected to the room and have that nick.
		"""
		
		return {bot_id: bot for bot_id, bot in self.bots.items()
		        if bot.roomname() == room and bot.mentionable() == nick}
