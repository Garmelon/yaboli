import time

from . import callbacks
from . import exceptions
from . import room

class Bot():
	"""
	Empty bot class that can be built upon.
	Takes care of extended botrulez.
	"""
	
	def __init__(self, roomname, nick="yaboli", password=None, manager=None):
		"""
		roomname - name of the room to connect to
		nick     - nick to assume, None -> no nick
		password - room password (in case the room is private)
		"""
		
		self.start_time = time.time()
		
		self.created_by = None
		self.created_in = None
		
		self.manager = manager
		
		# modify/customize this in your __init__() function (or anywhere else you want, for that matter)
		self.bot_description = ("This bot complies with the botrulez™ (https://github.com/jedevc/botrulez),\n"
		                        "plus a few extra commands.")
		
		self.helptexts = {}
		self.detailed_helptexts = {}
		
		self.room = room.Room(roomname, nick=nick, password=password)
		self.room.add_callback("message", self.on_message)
		
		self.commands = callbacks.Callbacks()
		
		self.add_command("clone", self.clone_command, "Clone this bot to another room.", # possibly add option to set nick?
		                 ("!clone @bot [ <room> [ --pw=<password> ] ]\n"
		                  "<room> : the name of the room to clone the bot to\n"
		                  "--pw : the room's password\n\n"
		                  "Clone this bot to the room specified.\n"
		                  "If the target room is passworded, you can use the --pw option to set\n"
		                  "a password for the bot to use.\n"
		                  "If no room is specified, this will use the current room and password."))
		
		self.add_command("help", self.help_command, "Show help information about the bot.",
		                 ("!help @bot [ -s | <command> ]\n"
		                  "-s : general syntax help\n\n"
		                  "Shows detailed help for a command if you specify a command name.\n"
		                  "Shows a list of commands and short description if no arguments are given."))
		
		self.add_command("kill", self.kill_command, "Kill (stop) the bot.",
		                 ("!kill @bot [ -r ]\n"
		                  "-r : restart the bot (will change the id)\n\n"
		                  "The bot disconnects from the room and stops."))
		
		self.add_command("ping", self.ping_command, "Replies 'Pong!'.",
		                 ("!ping @bot\n\n"
		                  "This command was originally used to help distinguish bots from\n"
		                  "people. Since the Great UI Change, this is no longer necessary as\n"
		                  "bots and people are displayed separately."))
		
		self.add_command("restart", self.restart_command, "Restart the bot (shorthand for !kill -r).",
		                 ("!restart @bot\n\n"
		                  "Restart the bot.\n"
		                  "Short for !kill @bot -r"))
		
		self.add_command("send", self.send_command, "Send the bot to another room.",
		                 ("!send @bot <room> [ --pw=<password> ]\n"
		                  "--pw : the room's password\n\n"
		                  "Sends this bot to the room specified. If the target room is passworded,\n"
		                  "you can use the --pw option to set a password for the bot to use."))
		
		self.add_command("uptime", self.uptime_command, "Show bot uptime since last (re-)start.",
		                 ("!uptime @bot [ -i ]\n"
		                  "-i : show more detailed information\n\n"
		                  "Shows the bot's uptime since the last start or restart.\n"
		                  "Shows additional information (i.e. id) if the -i flag is set."))
		
		
		self.add_command("show", self.show_command, detailed_helptext="You've found a hidden command! :)")
		
		self.room.launch()
	
	def stop(self):
		"""
		stop() -> None
		
		Kill this bot.
		"""
		
		self.room.stop()
	
	def add_command(self, command, function, helptext=None, detailed_helptext=None):
		"""
		add_command(command, function, helptext, detailed_helptext) -> None
		
		Subscribe a function to a command and add a help text.
		If no help text is provided, the command won't be displayed by the !help command.
		
		You can "hide" commands by specifying only the detailed helptext,
		or no helptext at all.
		"""
		
		command = command.lower()
		
		self.commands.add(command, function)
		
		if helptext:
			self.helptexts[command] = helptext
		
		if detailed_helptext:
			self.detailed_helptexts[command] = detailed_helptext
	
	def call_command(self, message):
		"""
		call_command(message) -> None
		
		Calls all functions subscribed to the command with the arguments supplied in the message.
		Deals with the situation that multiple bots of the same type and name are in the same room.
		"""
		
		try:
			command, bot_id, name, arguments, flags, options = self.parse(message.content)
		except exceptions.ParseMessageException:
			return
		
		if not self.commands.exists(command):
			return
		
		if not name == self.mentionable().lower():
			return
		
		name = self.room.mentionable(name).lower()
		
		if bot_id is not None: # id specified
			if self.manager.get(bot_id) == self:
				self.commands.call(command, message, arguments, flags, options)
			else:
				return
		
		else: # no id specified
			bots = self.manager.get_similar(self.roomname(), name)
			if self.manager.get_id(self) == min(bots): # only one bot should display the messages
				if len(bots) > 1:
					msg = ("There are multiple bots with that name in this room. To select one,\n"
					       "please specify its id (from the list below) as follows:\n"
					       "!{} <id> @{} [your arguments...]\n").format(command, name)
					
					for bot_id in sorted(bots):
						bot = bots[bot_id]
						msg += "\n{} - @{} ({})".format(bot_id, bot.nick(), bot.creation_info())
					
					self.room.send_message(msg, parent=message.id)
			
				else: # name is unique
					self.commands.call(command, message, arguments, flags, options)
	
	def roomname(self):
		"""
		roomname() -> roomname
		
		The room the bot is connected to.
		"""
		
		return self.room.room
	
	def nick(self):
		"""
		nick() -> nick
		
		The bot's full nick.
		"""
		
		return self.room.nick
	
	def mentionable(self):
		"""
		mentionable() -> nick
		
		The bot's nick in a mentionable format.
		"""
		
		return self.room.mentionable()
	
	def creation_info(self):
		"""
		creation_info() -> str
		
		Formatted info about the bot's creation
		"""
		
		ftime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.start_time))
		info = "created {}".format(ftime)
		
		if self.created_by:
			info += " by @{}".format(self.created_by)
		
		if self.created_in:
			info += " in &{}".format(self.created_in)
		
		return info
	
	def uptime(self):
		"""
		uptime() -> str
		
		Formatted uptime
		"""
		
		delta = int(time.time() - self.start_time)
		uptime = ""
		
		if delta >= 24*60*60:
			uptime +="{}d ".format(delta//(24*60*60))
			delta %= 24*60*60
			
		if delta >= 60*60:
			uptime += "{}h ".format(delta//(60*60))
			delta %= 60*60
		
		if delta >= 60:
			uptime += "{}m ".format(delta//60)
			delta %= 60
		
		uptime += "{}s".format(delta)
		
		return uptime
	
	def parse_command(self, message):
		"""
		parse_command(message_content) -> command, bot_id, name, argpart
		
		Parse the "!command[ bot_id] @botname[ argpart]" part of a command.
		"""
		
		# command name (!command)
		split = message.split(maxsplit=1)
		
		if split[0][:1] != "!":
			raise exceptions.ParseMessageException("Not a command")
		elif not len(split) > 1:
			raise exceptions.ParseMessageException("No bot name")
		
		command = split[0][1:].lower()
		message = split[1]
		split = message.split(maxsplit=1)
		
		# bot id
		try:
			bot_id = int(split[0])
		except ValueError:
			bot_id = None
		else:
			if not len(split) > 1:
				raise exceptions.ParseMessageException("No bot name")
			
			message = split[1]
			split = message.split(maxsplit=1)
		
		# bot name (@mention)
		if split[0][:1] != "@":
			raise exceptions.ParseMessageException("No bot name")
		
		name = split[0][1:].lower()
		
		# arguments to the command
		if len(split) > 1:
			argpart = split[1]
		else:
			argpart = None
		
		return command, bot_id, name, argpart
	
	def parse_arguments(self, argstr):
		"""
		parse_arguments(argstr) -> arguments, flags, options
		
		Parse the argument part of a command.
		"""
		
		argstr += " " # so the last argument will also be captured
		
		escaping = False
		quot_marks = None
		type_signs = 0
		option = None
		word = ""
		
		arguments = []
		flags = ""
		options = {}
		
		for char in argstr:
			
			# backslash-escaping
			if escaping:
				word += char
				escaping = False
			elif char == "\\":
				escaping = True
			
			# quotation mark escaped strings
			elif quot_marks:
				if char == quot_marks:
					quot_marks = None
				else:
					word += char
			elif char in ['"', "'"]:
				quot_marks = char
			
			# type signs
			elif char == "-":
				if type_signs < 2 and not word:
					type_signs += 1
				else:
					word += char
			
			# "=" in options
			elif char == "=" and type_signs == 2 and word and not option:
				option = word
				word = ""
			
			# space - evaluate information collected so far
			elif char == " ":
				if word:
					if type_signs == 0: # argument
						arguments.append(word)
					elif type_signs == 1: # flag(s)
						for flag in word:
							if not flag in flags:
								flags += flag
					elif type_signs == 2: # option
						if option:
							options[option] = word
						else:
							options[word] = True
				
				# reset all state variables
				escaping = False
				quot_marks = None
				type_signs = 0
				option = None
				word = ""
			
			# all other chars and situations
			else:
				word += char
		
		return arguments, flags, options
	
	def parse(self, message):
		"""
		parse(message_content) -> bool
		
		Parse a message.
		"""
		
		command, bot_id, name, argpart = self.parse_command(message)
		
		if argpart:
			arguments, flags, options = self.parse_arguments(argpart)
		else:
			arguments = []
			flags = ""
			options = {}
		
		return command, bot_id, name, arguments, flags, options
	
	# ----- HANDLING OF EVENTS -----
	
	def on_message(self, message):
		"""
		on_message(message) -> None
		
		Gets called when a message is received (see __init__).
		If you want to add a command to your bot, consider using add_command instead of overwriting
		this function.
		"""
		
		self.call_command(message)
	
	# ----- COMMANDS -----
	
	def clone_command(self, message, arguments, flags, options):
		"""
		clone_command(message, *arguments, flags, options) -> None
		
		Create a new bot.
		"""
		
		if not arguments:
			room = self.roomname()
			password = self.room.password
		else:
			room = arguments[0]
			
			if room[:1] == "&":
				room = room[1:]
			
			if "pw" in options and options["pw"] is not True:
				password = options["pw"]
			else:
				password = None
			
		try:
			bot = self.manager.create(room, password=password)
		except exceptions.CreateBotException:
			self.room.send_message("Bot could not be cloned.", parent=message.id)
		else:
			bot.created_in = self.roomname()
			bot.created_by = self.room.mentionable(message.sender.name)
			
			self.room.send_message("Cloned @{} to &{}.".format(bot.mentionable(), room),
			                       parent=message.id)
	
	def help_command(self, message, arguments, flags, options):
		"""
		help_command(message, *arguments, flags, options) -> None
		
		Show help about the bot.
		"""
		
		if arguments: # detailed help for one command
			command = arguments[0]
			if command[:1] == "!":
				command = command[1:]
			
			if command in self.detailed_helptexts:
				msg = "Detailed help for !{}:".format(command)
				msg += self.detailed_helptexts[command]
			else:
				msg = "No detailed help text found for !{}.".format(command)
				if command in self.helptexts:
					msg += "\n\n" + self.helptexts[command]
		
		elif "s" in flags: # detailed syntax help
			msg = "SYNTAX HELP PLACEHOLDER"
		
		else: # just list all commands
			msg = self.bot_description
			msg += "\n\nThis bot supports the following commands:"
			
			for command in sorted(self.helptexts):
				helptext = self.helptexts[command]
				msg += "\n!{} - {}".format(command, helptext)
			
			msg += ("\n\nFor help on the command syntax, try: !help @{0} -s\n"
			        "For detailed help on a command, try: !help @{0} <command>")
			msg = msg.format(self.mentionable())
		
		self.room.send_message(msg, parent=message.id)
	
	def kill_command(self, message, arguments, flags, options):
		"""
		kill_command(message, *arguments, flags, options) -> None
		
		stop the bot.
		"""
		
		if "r" in flags:
			bot = self.manager.create(self.roomname())
			bot.created_by = self.created_by
			bot.created_in = self.created_in
		
		self.room.send_message("/me exits.", message.id)
		
		self.manager.remove(self.manager.get_id(self))
	
	def ping_command(self, message, arguments, flags, options):
		"""
		ping_command(message, *arguments, flags, options) -> None
		
		Send a "Pong!" reply on a !ping command.
		"""
		
		self.room.send_message("Pong!", parent=message.id)
	
	def restart_command(self, message, arguments, flags, options):
		"""
		restart_command(message, *arguments, flags, options) -> None
		
		Restart the bot (shorthand for !kill @bot -r).
		"""
		
		self.commands.call("kill", message, [], "r", {})
	
	def send_command(self, message, arguments, flags, options):
		"""
		_command(message, *arguments, flags, options) -> None
		
		Send this bot to another room.
		"""
		
		if not arguments:
			return
		else:
			room = arguments[0]
			
			if room[:1] == "&":
				room = room[1:]
		
		if "pw" in options and options["pw"] is not True:
			password = options["pw"]
		else:
			password = None
		
		self.room.send_message("/me moves to &{}.".format(room), parent=message.id)
		
		self.room.change(room, password=password)
		self.room.launch()
	
	def show_command(self, message, arguments, flags, options):
		"""
		show_command(message, arguments, flags, options) -> None
		
		Show arguments, flags and options.
		"""
		
		msg = "arguments: {}\nflags: {}\noptions: {}".format(arguments, repr(flags), options)
		self.room.send_message(msg, parent=message.id)
	
	def uptime_command(self, message, arguments, flags, options):
		"""
		uptime_command(message, arguments, flags, options) -> None
		
		Show uptime and other info.
		"""
		
		msg = "uptime: {}".format(self.uptime())
		
		if "i" in flags:
			msg += "\nid: {}".format(self.manager.get_id(self))
			msg += "\n{}".format(self.creation_info())
		
		self.room.send_message(msg, message.id)
