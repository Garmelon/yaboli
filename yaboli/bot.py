import logging
import re
import time

from .cookiejar import *
from .room import *
from .utils import *


logger = logging.getLogger(__name__)
__all__ = ["Bot", "command", "trigger"]


# Some command stuff

SPECIFIC_RE = re.compile(r"!(\S+)\s+@(\S+)\s*([\S\s]*)")
GENERAL_RE = re.compile(r"!(\S+)\s*([\S\s]*)")

# Decorator magic for commands and triggers.
# I think commands could probably be implemented as some kind of triggers,
# but I'm not gonna do that now because commands are working fine this way.
def command(commandname, specific=True, args=True):
	def decorator(func):
		async def wrapper(self, room, message, *args_, **kwargs_):
			if specific:
				result = self._parse_command(message.content, specific=room.session.nick)
			else:
				result = self._parse_command(message.content)
			if result is None: return False
			cmd, argstr = result
			if cmd != commandname: return False
			if args:
				await func(self, room, message, argstr, *args_, **kwargs_)
				return True
			else:
				if argstr: return
				await func(self, room, message, *args_, **kwargs_)
				return True
		return wrapper
	return decorator

def trigger(regex, fullmatch=True, flags=0):
	def decorator(func):
		compiled_regex = re.compile(regex, flags=flags)
		async def wrapper(self, room, message, *args, **kwargs):
			if fullmatch:
				match = compiled_regex.fullmatch(message.content)
			else:
				match = compiled_regex.match(message.content)
			if match is not None:
				await func(self, room, message, match, *args, **kwargs)
				return True
			else:
				return False
		return wrapper
	return decorator


# And now comes the real bot...

class Bot(Inhabitant):
	def __init__(self, nick, cookiefile=None):
		self.target_nick = nick
		self.rooms = {}
		self.cookiejar = CookieJar(cookiefile)

	# ROOM MANAGEMENT

	def join_room(self, roomname, **kwargs):
		if roomname in self.rooms:
			return

		self.rooms[roomname] = Room(self, roomname, self.target_nick, cookiejar=self.cookiejar, **kwargs)

	async def part_room(self, roomname):
		room = self.rooms.pop(roomname, None)
		if room:
			await room.exit()

	# INHABITED FUNCTIONS

	async def on_stopped(self, room):
		await self.part_room(room.roomname)

	# BOTRULEZ

	@command("ping", specific=False, args=False)
	async def botrulez_ping_general(self, room, message, text="Pong!"):
		await room.send(text, message.mid)

	@command("ping", specific=True, args=False)
	async def botrulez_ping_specific(self, room, message, text="Pong!"):
		await room.send(text, message.mid)

	@command("help", specific=False, args=False)
	async def botrulez_help_general(self, room, message, text="Placeholder help text"):
		await room.send(text, message.mid)

	@command("help", specific=True, args=False)
	async def botrulez_help_specific(self, room, message, text="Placeholder help text"):
		await room.send(text, message.mid)

	@command("uptime", specific=True, args=False)
	async def botrulez_uptime(self, room, message):
		now = time.time()
		startformat = format_time(room.start_time)
		deltaformat = format_time_delta(now - room.start_time)
		text = f"/me has been up since {startformat} ({deltaformat})"
		await room.send(text, message.mid)

	@command("kill", specific=True, args=False)
	async def botrulez_kill(self, room, message, text="/me dies"):
		await room.send(text, message.mid)
		await self.part_room(room.roomname)

	@command("restart", specific=True, args=False)
	async def botrulez_restart(self, room, message, text="/me restarts"):
		await room.send(text, message.mid)
		await self.part_room(room.roomname)
		self.join_room(room.roomname, password=room.password)

	# COMMAND PARSING

	@staticmethod
	def parse_args(text):
		"""
		Use bash-style single- and double-quotes to include whitespace in arguments.
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

	@staticmethod
	def parse_flags(arglist):
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

	@staticmethod
	def _parse_command(content, specific=None):
		if specific is not None:
			match = SPECIFIC_RE.fullmatch(content)
			if match and similar(match.group(2), specific):
				return match.group(1), match.group(3)
		else:
			match = GENERAL_RE.fullmatch(content)
			if match:
				return match.group(1), match.group(2)
