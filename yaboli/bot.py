from . import callbacks
import time

from . import room
from . import exceptions

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
		
		self.helptexts = {}
		self.detailed_helptexts = {}
		
		self.room = room.Room(roomname, nick=nick, password=password)
		self.room.add_callback("message", self.on_message)
		
		self.commands = callbacks.Callbacks()
		#self.commands.add("create", create_command)
		#self.commands.add("kill",     kill_command)
		#self.commands.add("send",     send_command)
		#self.commands.add("uptime", uptime_command)
		
		self.add_command("help", self.help_command, "Shows help information about the bot.",
		                 ("!help @bot [ -s | <command> ]\n"
		                  "-s : general syntax help\n\n"
		                  "Shows detailed help for a command if you specify a command name.\n"
		                  "Shows a list of commands and short description if no arguments are given."))
		
		self.add_command("ping", self.ping_command, "Replies 'Pong!'.",
		                 ("!ping @bot\n\n"
		                  "This command was originally used to help distinguish bots from\n"
		                  "people. Since the Great UI Change, this is no longer necessary as\n"
		                  "bots and people are displayed separately."))
		
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
		
		if not name == self.room.session.mentionable():
			return
		
		if bot_id is not None: # id specified
			if self.manager.get(bot_id) == self:
				self.commands.call(command, message, arguments, flags, options)
			else:
				return
		
		else: # no id specified
			bots = self.manager.get_similar(self.get_room(), name)
			if self.manager.get_id(self) == min(bots):
				if len(bots) > 1:
					msg = ("There are multiple bots with that name in this room. To select one,\n"
					       "please specify its id (from the list below) as follows:\n"
					       "!{} <id> @{} [your arguments...]\n").format(command, name)
					
					for bot_id in sorted(bots):
						bot = bots[bot_id]
						msg += "\n{} - @{} ({})".format(bot_id, bot.get_nick(), bot.creation_info())
					
					self.room.send_message(msg, parent=message.id)
			
				else: # name is unique
					self.commands.call(command, message, arguments, flags, options)
	
	def get_room(self):
		"""
		get_room() -> roomname
		
		The room the bot is connected to.
		"""
		
		return self.room.room
	
	def get_mentionable_nick(self):
		"""
		get_mentionable_nick() -> nick
		
		The The bot's nick in a mentionable format.
		"""
		
		if self.room.session:
			return self.room.session.mentionable()
	
	def get_nick(self):
		"""
		get_nick() -> nick
		
		The bot's nick.
		"""
		
		if self.room.session:
			return self.room.session.name
	
	def creation_info(self):
		"""
		creation_info() -> str
		
		Formatted info about the bot's creation
		"""
		
		ftime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.start_time))
		info = "created at {}".format(ftime)
		
		if self.created_by:
			info += " by @{}".format(self.created_by)
		
		if self.created_in:
			info += " in &{}".format(self.created_in)
		
		return info
	
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
	
	def help_command(self, message, arguments, flags, options):
		"""
		help_command(message, *arguments, flags, options) -> None
		
		Show help about the bot.
		"""
		
		if "s" in flags: # detailed syntax help
			msg = "SYNTAX HELP PLACEHOLDER"
		
		elif arguments: # detailed help for one command
			command = arguments[0]
			if command[:1] == "!":
				command = command[1:]
			
			if command in self.detailed_helptexts:
				msg = self.detailed_helptexts[command]
			else:
				msg = "No detailed help text found for !{}.".format(command)
				if command in self.helptexts:
					msg += "\n\n" + self.helptexts[command]
		
		else: # just list all commands
			msg = "This bot supports the following commands:\n"
			
			for command in sorted(self.helptexts):
				helptext = self.helptexts[command]
				msg += "\n!{} - {}".format(command, helptext)
			
			msg += ("\n\nFor detailed help on the command syntax, try:\n"
			        "!help @{0} -s\n"
			        "For detailed help on a command, try:\n"
			        "!help {0} <command>").format(self.get_mentionable_nick())
		
		self.room.send_message(msg, parent=message.id)
	
	def ping_command(self, message, arguments, flags, options):
		"""
		ping_command(message, *arguments, flags, options) -> None
		
		Send a "Pong!" reply on a !ping command.
		"""
		
		self.room.send_message("Pong!", parent=message.id)
	
	def show_command(self, message, arguments, flags, options):
		"""
		show_command(message, arguments, flags, options) -> None
		
		Show arguments, flags and options.
		"""
		
		msg = "arguments: {}\nflags: {}\noptions: {}".format(arguments, repr(flags), options)
		self.room.send_message(msg, parent=message.id)
