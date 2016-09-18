import json
import logging
logger = logging.getLogger(__name__)

class BotManager:
	"""
	Keep track of multiple bots in different rooms.
	Save and load bots from a file.
	"""
	
	def __init__(self, bot_class, bot_limit=None):
		"""
		
		"""
		self.bot_class = bot_class
		self.bot_limit = bot_limit
		self.bot_id_counter = 0 # no two bots can have the same id
		self.bots = {} # each bot has an unique id
	
	def create(self, name, room, pw=None, creator=None, create_room=None, create_time=None):
		"""
		create(name, room, pw, creator, create_room, create_time) -> bot
		
		Create a bot of type self.bot_class.
		Starts the bot and returns it.
		"""
		
		bot_id = self.bot_id_counter
		self.bot_id_counter += 1
		
		bot = self.bot_class(name=name, room=room, pw=pw, creator=creator,
		                     create_room=create_room, create_time=create_time)
		
		self.bots[bot_id] = bot
		bot.run(self)
		
		logger.info("Created {}: {} in room {}".format(bot_id, name, room))
		return bot
	
	def remove(self, bot_id):
		"""
		remove(bot_id) -> None
		
		Remove a bot from the manager and stop it.
		"""
		
		bot = self.get(bot_id)
		if not bot: return
	
		# for logging purposes
		name = bot.get_name()
		room = bot.get_roomname()
		
		bot.stop()
		del self.bots[bot_id]
		
		logger.info("Removed {}: {} in room {}".format(bot_id, name, room))
	
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
			if bot.get_roomname() == roomname and mention.equals(bot.get_name()):
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
				"name": bot.get_name(),
				"room": bot.get_roomname(),
				"pw":   bot.get_roompw(),
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
				self.create(bot_info["name"], bot_info["room"], bot_info["pw"], bot_info["creator"],
				            bot_info["create_room"], bot_info["create_time"]).load(bot_info["data"])
		
		logger.info("Loaded bots.")
	
	def interactive(self):
		"""
		interactive() -> None
		
		Start interactive mode that allows you to manage bots using commands.
		Command list:
		[NYI]
		"""
		
		pass
