import json
import time
import logging
logger = logging.getLogger(__name__)

from .exceptions import CreateBotException
from .mention import Mention

class BotManager:
	"""
	Keep track of multiple bots in different rooms.
	Save and load bots from a file.
	
	If you've created a bot from the Bot class, you can easily host it by adding:
	
	if __name__ == "__main__":
		manager = BotManager(YourBotClass, bot_limit=10)
		manager.interactive()
	
	to your file and then executing it.
	"""
	
	def __init__(self, bot_class, bot_limit=None):
		"""
		bot_class - bot class you want to run
		bot_limit - maximum amount of bots to exist simultaneously
		"""
		
		self.bot_class = bot_class
		self.bot_limit = bot_limit
		self.bot_id_counter = 0 # no two bots can have the same id
		self.bots = {} # each bot has an unique id
	
	def create(self, nick, roomname, password=None, creator=None, create_room=None, create_time=None):
		"""
		create(nick, roomname, password, creator, create_room, create_time) -> bot
		
		Create a bot of type self.bot_class.
		Starts the bot and returns it.
		"""
		
		if self.bot_limit and len(self.bots) >= self.bot_limit:
			raise CreateBotException("Bot limit hit ({} bots)".format(self.bot_limit))
		
		bot_id = self.bot_id_counter
		self.bot_id_counter += 1
		
		if create_time is None:
			create_time = time.time()
		
		bot = self.bot_class(nick, roomname, password=password, creator=creator, create_room=create_room,
		                     create_time=create_time, manager=self)
		
		self.bots[bot_id] = bot
		bot.launch()
		
		logger.info("Created {} - {} in room {}".format(bot_id, nick, roomname))
		return bot
	
	def remove(self, bot_id):
		"""
		remove(bot_id) -> None
		
		Remove a bot from the manager and stop it.
		"""
		
		bot = self.get(bot_id)
		if not bot: return
	
		# for logging purposes
		nick = bot.get_nick()
		roomname = bot.get_roomname()
		
		bot.stop()
		del self.bots[bot_id]
		
		logger.info("Removed {} - {} in room {}".format(bot_id, nick, roomname))
	
	def get(self, bot_id):
		"""
		get(bot_id) -> bot
		
		Get a bot by its id.
		Returns None if no bot was found.
		"""
		
		return self.bots.get(bot_id)
	
	def get_id(self, bot):
		"""
		get_id(bot) -> bot_id
		
		Get a bot's id.
		Returns None if id not found.
		"""
		
		for bot_id, lbot in self.bots.items():
			if lbot == bot:
				return bot_id
	
	def similar(self, roomname, mention):
		"""
		in_room(roomname, mention) -> [bot_id]
		
		Get all bots that are connected to a room and match the mention.
		The bot ids are sorted from small to big.
		"""
		
		l = []
		
		for bot_id, bot in sorted(self.bots.items()):
			if bot.get_roomname() == roomname and mention == Mention(bot.get_nick()):
				l.append(bot_id)
		
		return l
	
	def save(self, filename):
		"""
		save(filename) -> None
		
		Save all current bots to a file.
		"""
		
		logger.info("Saving bots to {}".format(filename))
		
		bots = []
		for bot in self.bots.values():
			bots.append({
				"nick": bot.get_nick(),
				"room": bot.get_roomname(),
				"password":   bot.get_roompassword(),
				"creator":     bot.get_creator(),
				"create_room": bot.get_create_room(),
				"create_time": bot.get_create_time(),
				"data": bot.save()
			})
		logger.debug("Bot info: {}".format(bots))
		
		logger.debug("Writing to file")
		with open(filename, "w") as f:
			json.dump(bots, f, sort_keys=True, indent=4)
		
		logger.info("Saved bots.")
	
	def load(self, filename):
		"""
		load(filename) -> None
		
		Load bots from a file.
		Creates the bots and starts them.
		"""
		
		logger.info("Loading bots from {}".format(filename))
		
		try:
			logger.debug("Reading file")
			with open(filename) as f:
				bots = json.load(f)
		
		except FileNotFoundError:
			logger.warning("File {} not found.".format(filename))
		
		else:
			logger.debug("Bot info: {}".format(bots))
			for bot_info in bots:
				try:
					self.create(bot_info["nick"], bot_info["room"], bot_info["password"],
					            bot_info["creator"], bot_info["create_room"],
					            bot_info["create_time"]).load(bot_info["data"])
				except CreateBotException as err:
					logger.warning("Creating bot failed: {}.".format(err))
		
		logger.info("Loaded bots.")
	
	def interactive(self):
		"""
		interactive() -> None
		
		Start interactive mode that allows you to manage bots using commands.
		Command list:
		[NYI]
		"""
		
		pass
