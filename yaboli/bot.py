import time

from . import callbacks
from . import room

class Bot:
	def __init__(self, nick, roomname, password=None, creator=None, create_room=None,
	             create_time=None, manager=None):
		"""
		nick        - nick to assume, None -> no nick
		roomname    - name of the room to connect to
		password    - room password (in case the room is private)
		creator     - nick of the person the bot was created by
		create_room - room the bot was created in
		create_time - time/date the bot was created at (used when listing bots)
		"""
		
		self.manager = manager
		self.start_time = time.time()
		
		self.creator = creator
		self.create_room = create_room
		self.create_time = create_time
		
		
		self.room = room.Room(nick, roomname, password=password)
		#self.room.add_callback("message", self.on_message)
		
		# description used on general "!help", and in the !help text. (None - no reaction)
		self.short_description = None
		self.description = ("This bot complies with the botrulez™",
		                    "(https://github.com/jedevc/botrulez),\n"
		                    "plus a few extra commands.")
		
		self._commands = callbacks.Callbacks()
		self._general_commands = [] # without @mention after the !nick
		self._specific_commands = [] # need to choose certain bot if multiple are present
		self._helptexts = {}
		self._detailed_helptexts = {}
	
	def launch(self):
		self.room.launch()
	
	def stop(self):
		self.room.stop()
	
	def get_nick(self):
		return self.room.nick
	
	def get_roomname(self):
		return self.room.roomname
	
	def get_roompassword(self):
		return self.room.password
	
	def get_creator(self):
		return self.creator
	
	def get_create_room(self):
		return self.create_room
	
	def get_create_time(self):
		return self.create_time
	
	@staticmethod
	def format_date(seconds, omit_date=False, omit_time=False):
		"""
		format_date(seconds) -> string
		
		Convert a date (Unix/POSIX/Epoch time) into a YYYY-MM-DD hh:mm:ss format.
		"""
		
		f = ""
		if not omit_date:
			f += "%Y-%m-%d"
		
		if not omit_time:
			if not omit_date: f += " "
			f += "%H:%M:%S"
			
		return time.strftime(f, time.gmtime(seconds))
	
	@staticmethod
	def format_delta(seconds):
		"""
		format_delta(seconds) -> string
		
		Convert a time difference into the following format (where x is an integer):
		[-] [[[xd ]xh ]xm ]xs
		"""
		
		seconds = int(seconds)
		delta = ""
		
		if seconds < 0:
			delta += "- "
			seconds = -seconds
		
		if seconds >= 24*60*60:
			delta +="{}d ".format(seconds//(24*60*60))
			seconds %= 24*60*60
			
		if seconds >= 60*60:
			delta += "{}h ".format(seconds//(60*60))
			seconds %= 60*60
		
		if seconds >= 60:
			delta += "{}m ".format(seconds//60)
			seconds %= 60
		
		delta += "{}s".format(seconds)
		
		return delta
	
	def uptime(self):
		"""
		uptime() -> string
		
		The bot's uptime since it was last started, in the following format:
		date time (delta)
		"""
		
		date = self.format_date(self.start_time)
		delta = self.format_delta(time.time() - self.start_time)
		
		return "{} ({})".format(date, delta)
	
	def save(self):
		"""
		Overwrite if your bot should save when BotManager is shut down.
		Make sure to also overwrite load().
		
		The data returned will be converted to json and back for using the json module, so
		make sure your data can handle that (i.e. don't use numbers as dict keys etc.)
		"""
		
		pass
	
	def load(self, data):
		"""
		Overwrite to load data from save().
		See save() for more details.
		"""
		
		pass
