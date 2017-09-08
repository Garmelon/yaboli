import asyncio
from collections import namedtuple
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
	
	ParsedMessage = namedtuple("ParsedMessage", ["command", "argstr"])
	TopicHelp = namedtuple("TopicHelp", ["text", "visible"])
	
	def __init__(self, nick):
		super().__init__(nick)
		
		self.restarting = False # whoever runs the bot can check if a restart is necessary
		self.start_time = time.time()
		
		self._commands = Callbacks()
		self._triggers = Callbacks()
		self.register_default_commands()
		
		self._help_topics = {}
		self.add_default_help_topics()
		
		# settings (modify in your bot's __init__)
		self.help_general = None # None -> does not respond to general help
		self.help_specific = "No help available"
		self.killable = True
		self.kill_message = "/me *poof*" # how to respond to !kill, whether killable or not
		self.restartable = True
		self.restart_message = "/me temporary *poof*" # how to respond to !restart, whether restartable or not
		self.ping_message = "Pong!" # as specified by the botrulez
	
	def register_command(self, command, callback, specific=True):
		self._commands.add((command, specific), callback)
	
	def register_trigger(self, regex, callback):
		self._triggers.add(regex, callback)
	
	def add_help(self, topic, text, visible=True):
		info = self.TopicHelp(text, visible)
		self._help_topics[topic] = info
	
	def get_help(self, topic):
		info = self._help_topics.get(topic, None)
		if info:
			return self.format_help(info.text)
	
	def format_help(self, helptext):
		return helptext.format(
			nick=mention(self.nick)
		)
	
	def list_help_topics(self, max_characters=100):
		# Magic happens here to ensure that the resulting lines are always
		# max_characters or less characters long.
		
		lines = []
		curline = ""
		wrapper = None
		
		for topic, info in sorted(self._help_topics.items()):
			if not info.visible:
				continue
			
			if wrapper:
				curline += ","
				lines.append(curline)
				curline = wrapper
				wrapper = None
			
			if not curline:
				curline = topic
			elif len(curline) + len(f", {topic},") <= max_characters:
				curline += f", {topic}"
			elif len(curline) + len(f", {topic}") <= max_characters:
				wrapper = topic
			else:
				curline += ","
				lines.append(curline)
				curline = topic
		
		if wrapper:
			curline += ","
			lines.append(curline)
			lines.append(wrapper)
		elif curline:
			lines.append(curline)
		
		return "\n".join(lines)
	
	async def restart(self):
		# After calling this, the bot is stopped, not yet restarted.
		self.restarting = True
		await self.stop()
	
	def noargs(func):
		async def wrapper(self, message, argstr):
			if not argstr:
				return await func(self, message)
		return wrapper
	
	async def on_send(self, message):
		wait = []
		
		# get specific command to call (if any)
		specific = self.parse_message(message.content, specific=True)
		if specific:
			wait.append(self._commands.call(
				(specific.command, True),
				message, specific.argstr
			))
		
		# get generic command to call (if any)
		general = self.parse_message(message.content, specific=False)
		if general:
			wait.append(self._commands.call(
				(general.command, False),
				message, general.argstr
			))
		
		# find triggers to call (if any)
		for trigger in self._triggers.list():
			match = re.fullmatch(trigger, message.content)
			if match:
				wait.append(self._triggers.call(trigger, message, match))
		
		if wait:
			await asyncio.wait(wait)
	
	def parse_message(self, content, specific=True):
		"""
		ParsedMessage = parse_message(content)
		
		Returns None, not a (None, None) tuple, when message could not be parsed
		"""
		
		if specific:
			match = re.fullmatch(self.SPECIFIC_RE, content)
			if match and similar(match.group(2), self.nick):
				return self.ParsedMessage(match.group(1), match.group(3))
		else:
			match = re.fullmatch(self.GENERIC_RE, content)
			if match:
				return self.ParsedMessage(match.group(1), match.group(2))
	
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
	
	def register_default_commands(self):
		self.register_command("ping", self.command_ping)
		self.register_command("ping", self.command_ping, specific=False)
		self.register_command("help", self.command_help)
		self.register_command("help", self.command_help_general, specific=False)
		self.register_command("uptime", self.command_uptime)
		self.register_command("kill", self.command_kill)
		self.register_command("restart", self.command_restart)
	
	def add_default_help_topics(self):
		self.add_help("botrulez", (
			"This bot complies with the botrulez at https://github.com/jedevc/botrulez.\n"
			"It implements the standard commands, and additionally !kill and !restart.\n\n"
			"Standard commands:\n"
			"  !ping, !ping @{nick} - reply with a short pong message\n"
			"  !help, !help @{nick} - reply with help about the bot\n"
			"  !uptime @{nick} - reply with the bot's uptime\n\n"
			"Non-standard commands:\n"
			"  !kill @{nick} - terminate this bot instance\n"
			"  !restart @{nick} - restart this bot instance\n\n"
			"Command extensions:\n"
			"  !help @{nick} <topic> [<topic> ...] - provide help on the topics listed"
		))
		
		self.add_help("yaboli", (
			"Yaboli is \"Yet Another BOt LIbrary for euphoria\", written by @Garmy in Python.\n"
			"It relies heavily on the asyncio module from the standard library and uses f-strings.\n"
			"Because of this, Python version >= 3.6 is required.\n\n"
			"Github: https://github.com/Garmelon/yaboli"
		))
	
	@noargs
	async def command_ping(self, message):
		if self.ping_message:
			await self.room.send(self.ping_message, message.mid)
	
	async def command_help(self, message, argstr):
		args = self.parse_args(argstr.lower())
		if not args:
			if self.help_specific:
				await self.room.send(
					self.format_help(self.help_specific),
					message.mid
				)
		else:
			# collect all valid topics
			messages = []
			for topic in sorted(set(args)):
				text = self.get_help(topic)
				if text:
					messages.append(f"Topic: {topic}\n{text}")
			
			# print result in separate messages
			if messages:
				for text in messages:
					await self.room.send(text, message.mid)
			else:
				await self.room.send("None of those topics found.", message.mid)
	
	@noargs
	async def command_help_general(self, message):
		if self.help_general is not None:
			await self.room.send(self.help_general, message.mid)
	
	@noargs
	async def command_uptime(self, message):
		now = time.time()
		startformat = format_time(self.start_time)
		deltaformat = format_time_delta(now - self.start_time)
		text = f"/me has been up since {startformat} ({deltaformat})"
		await self.room.send(text, message.mid)
	
	async def command_kill(self, message, args):
		logging.warn(f"Kill attempt by @{mention(message.sender.nick)} in &{self.room.roomname}: {message.content!r}")
		
		if self.kill_message is not None:
			await self.room.send(self.kill_message, message.mid)
		
		if self.killable:
			await self.stop()
	
	async def command_restart(self, message, args):
		logging.warn(f"Restart attempt by @{mention(message.sender.nick)} in &{self.room.roomname}: {message.content!r}")
		
		if self.restart_message is not None:
			await self.room.send(self.restart_message, message.mid)
		
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
