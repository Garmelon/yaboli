import asyncio
import logging
import re
from .callbacks import *
from .controller import *

logger = logging.getLogger(__name__)
__all__ = ["Bot"]



class Bot(Controller):
	# ^ and $ not needed since we're doing a re.fullmatch
	SPECIFIC_RE = r"!(\S+)\s+@(\S+)([\S\s]*)"
	GENERIC_RE = r"!(\S+)([\S\s]*)"
	
	def __init__(self, nick):
		super().__init__(nick)
		
		self._callbacks = Callbacks()
		self.register_default_callbacks()
	
	def register_callback(self, event, callback, specific=True):
		self._callbacks.add((event, specific), callback)
	
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
			mention = args[0]
			args = args[1:]
			if mention[:1] == "@" and similar(mention[1:], self.nick):
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
			elif character.isspace() and len(arg) > 0:
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
	
	
	
	# BOTRULEZ COMMANDS
	
	def register_default_callbacks(self):
		self.register_callback("ping", self.command_ping)
		self.register_callback("ping", self.command_ping, specific=False)
	
	async def command_ping(self, message, args):
		await self.room.send("Pong!", message.message_id)
