import asyncio
import logging
import re
import time
from .callbacks import *
from .controller import *
from .utils import *

logger = logging.getLogger(__name__)
__all__ = ["Bot"]



class Bot(Controller):
	# ^ and $ not needed since we're doing a re.fullmatch
	SPECIFIC_RE = r"!(\S+)\s+@(\S+)([\S\s]*)"
	GENERIC_RE = r"!(\S+)([\S\s]*)"
	
	def __init__(self, nick):
		super().__init__(nick)
		
		self.restarting = False # whoever runs the bot can check if a restart is necessary
		self.start_time = time.time()
		
		self._callbacks = Callbacks()
		self.register_default_callbacks()
		
		self._help_topics = {}
		
		# settings (modify in your bot's __init__)
		self.help_general = None # None -> does not respond to general help
		self.help_specific = "No help available"
		self.killable = True
		self.kill_message = "/me *poof*" # how to respond to !kill, whether killable or not
		self.restartable = True
		self.restart_message = "/me temporary *poof*" # how to respond to !restart, whether restartable or not
		self.ping_message = "Pong!" # as specified by the botrulez
	
	def register_callback(self, event, callback, specific=True):
		self._callbacks.add((event, specific), callback)
	
	def add_help(self, topic, text, description=None):
		info = (text, description) # TODO: make named tuple?
		self._help_topics[topic] = info
	
	def get_help(self, topic):
		info = self._help_topics.get(topic, ("No help available", None))
		return info[0]
	
	def get_help_topics(self):
		topics = []
		for topic, info in sorted(self._help_topics.items()):
			if info[1] is not None:
				topics.append(f"{topic} - {info[1]}\n")
		return "".join(topics)
	
	async def restart(self):
		# After calling this, the bot is stopped, not yet restarted.
		self.restarting = True
		await self.stop()
	
	def noargs(func):
		async def wrapper(self, message, args):
			if not args:
				return await func(self, message)
		return wrapper
	
	async def on_send(self, message):
		parsed = self.parse_message(message.content)
		if not parsed:
			return
		command, args = parsed
		
		# general callback (specific set to False)
		general = asyncio.ensure_future(
			self._callbacks.call((command, False), message, args)
		)
		
		if len(args) > 0:
			name = args[0]
			args = args[1:]
			if name[:1] == "@" and similar(name[1:], self.nick):
				logger.debug("Specific command!")
				# specific callback (specific set to True)
				await self._callbacks.call((command, True), message, args)
		
		await general
	
	def parse_message(self, content):
		"""
		(command, args) = parse_message(content)
		
		Returns None, not a (None, None) tuple, when message could not be parsed
		"""
		
		match = re.fullmatch(self.GENERIC_RE, content)
		if not match:
			return None
		
		command = match.group(1)
		argstr = match.group(2)
		args = self.parse_args(argstr)
		
		logger.debug(f"Parsed command. command={command!r}, args={args!r}")
		
		return command, args
	
	def parse_args(self, text):
		"""
		Use single- and double-quotes bash-style to include whitespace in arguments.
		A backslash always escapes the next character.
		Any non-escaped whitespace separates arguments.
		
		Returns a list of arguments.
		Deals with unclosed quotes and backslashes without crashing.
		"""
		
		escape = False
		quote = None
		args = []
		arg = ""
		
		for character in text:
			if escape:
				arg += character
				escape = False
			elif character == "\\":
				escape = True
			elif quote:
				if character == quote:
					quote = None
				else:
					arg += character
			elif character in "'\"":
				quote = character
			elif character.isspace():
				if len(arg) > 0:
					args.append(arg)
					arg = ""
			else:
				arg += character
				
		#if escape or quote:
			#return None # syntax error
		
		if len(arg) > 0:
			args.append(arg)
			
		return args
	
	def parse_flags(self, arglist):
		flags = ""
		args = []
		kwargs = {}
		
		for arg in arglist:
			# kwargs (--abc, --foo=bar)
			if arg[:2] == "--":
				arg = arg[2:]
				if "=" in arg:
					s = arg.split("=", maxsplit=1)
					kwargs[s[0]] = s[1]
				else:
					kwargs[arg] = None
			# flags (-x, -rw)
			elif arg[:1] == "-":
				arg = arg[1:]
				flags += arg
			# args (normal arguments)
			else:
				args.append(arg)
		
		return flags, args, kwargs
	
	
	
	# BOTRULEZ AND YABOLI-SPECIFIC COMMANDS
	
	def register_default_callbacks(self):
		self.register_callback("ping", self.command_ping)
		self.register_callback("ping", self.command_ping, specific=False)
		self.register_callback("help", self.command_help)
		self.register_callback("help", self.command_help_general, specific=False)
		self.register_callback("uptime", self.command_uptime)
		self.register_callback("kill", self.command_kill)
		self.register_callback("restart", self.command_restart)
	
	@noargs
	async def command_ping(self, message):
		if self.ping_message:
			await self.room.send(self.ping_message, message.message_id)
	
	@noargs # TODO: specific command help (!help @bot ping)
	async def command_help(self, message):
		if self.help_specific:
			await self.room.send(self.help_specific, message.message_id)
	
	@noargs
	async def command_help_general(self, message):
		if self.help_general is not None:
			await self.room.send(self.help_general, message.message_id)
	
	@noargs
	async def command_uptime(self, message):
		now = time.time()
		startformat = format_time(self.start_time)
		deltaformat = format_time_delta(now - self.start_time)
		text = f"/me has been up since {startformat} ({deltaformat})"
		await self.room.send(text, message.message_id)
	
	async def command_kill(self, message, args):
		logging.warn(f"Kill attempt by @{mention(message.sender.nick)} in &{self.room.roomname}: {message.content!r}")
		
		if self.kill_message is not None:
			await self.room.send(self.kill_message, message.message_id)
		
		if self.killable:
			await self.stop()
	
	async def command_restart(self, message, args):
		logging.warn(f"Restart attempt by @{mention(message.sender.nick)} in &{self.room.roomname}: {message.content!r}")
		
		if self.restart_message is not None:
			await self.room.send(self.restart_message, message.message_id)
		
		if self.restartable:
			await self.restart()

class Multibot(Bot):
	def __init__(self, nick, keeper):
		super().__init__(nick)
		
		self.keeper = keeper

class MultibotKeeper():
	def __init__(self, configfile):
		# TODO: load configfile
		
		# TODO: namedtuple botinfo (bot, task)
		self._bots = {} # self._bots[roomname] = botinfo
