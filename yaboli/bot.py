import logging
import re
import time

from .cookiejar import *
from .room import *
from .utils import *


logger = logging.getLogger(__name__)
__all__ = ["Bot", "command", "trigger", "Module", "ModuleBot"]


# Some command stuff

SPECIFIC_RE = re.compile(r"!(\S+)\s+@(\S+)\s*([\S\s]*)")
GENERAL_RE = re.compile(r"!(\S+)\s*([\S\s]*)")

# Decorator magic for commands and triggers.
# I think commands could probably be implemented as some kind of triggers,
# but I'm not gonna do that now because commands are working fine this way.
def command(*commands):
	def decorator(func):
		async def wrapper(self, room, message, command, *args, **kwargs):
			if command in commands:
				await func(self, room, message, *args, **kwargs)
				return True
			else:
				return False
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

	# COMMANDS

	async def on_command_specific(self, room, message, command, nick, argstr):
		pass

	async def on_command_general(self, room, message, command, argstr):
		pass

	# INHABITED FUNCTIONS

	async def on_send(self, room, message):
		match = SPECIFIC_RE.fullmatch(message.content)
		if match:
			command, nick, argstr = match.groups()
			await self.on_command_specific(room, message, command, nick, argstr)

		match = GENERAL_RE.fullmatch(message.content)
		if match:
			command, argstr = match.groups()
			await self.on_command_general(room, message, command, argstr)

	async def on_stopped(self, room):
		await self.part_room(room.roomname)

	# BOTRULEZ

	@command("ping")
	async def botrulez_ping(self, room, message, text="Pong!"):
		await room.send(text, message.mid)

	@command("help")
	async def botrulez_help(self, room, message, text="Placeholder help text"):
		await room.send(text, message.mid)

	@command("uptime")
	async def botrulez_uptime(self, room, message):
		now = time.time()
		startformat = format_time(room.start_time)
		deltaformat = format_time_delta(now - room.start_time)
		text = f"/me has been up since {startformat} ({deltaformat})"
		await room.send(text, message.mid)

	@command("kill")
	async def botrulez_kill(self, room, message, text="/me dies"):
		await room.send(text, message.mid)
		await self.part_room(room.roomname)

	@command("restart")
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

		if escape:
			arg += "\\"

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
		if specific:
			match = SPECIFIC_RE.fullmatch(content)
			if match:
				return match.group(1), match.group(3)
		else:
			match = GENERAL_RE.fullmatch(content)
			if match:
				return match.group(1), match.group(2)

class Module(Inhabitant):
	SHORT_DESCRIPTION = "short module description"
	LONG_DESCRIPTION = "long module description"
	SHORT_HELP = "short !help"
	LONG_HELP = "long !help"

	async def on_command_specific(self, room, message, command, nick, argstr, mentioned):
		pass

	async def on_command_general(self, room, message, command, argstr):
		pass

class ModuleBot(Bot):
	def __init__(self, module, nick, *args, cookiefile=None, **kwargs):
		super().__init__(nick, cookiefile=cookiefile)
		self.module = module

	async def on_created(self, room):
		await self.module.on_created(room)

	async def on_connected(self, room, log):
		await self.module.on_connected(room, log)

	async def on_disconnected(self, room):
		await self.module.on_disconnected(room)

	async def on_stopped(self, room):
		await self.module.on_stopped(room)

	async def on_join(self, room, session):
		await self.module.on_join(room, session)

	async def on_part(self, room, session):
		await self.module.on_part(room, session)

	async def on_nick(self, room, sid, uid, from_nick, to_nick):
		await self.module.on_nick(room, sid, uid, from_nick, to_nick)

	async def on_send(self, room, message):
		await super().on_send(room, message)

		await self.module.on_send(room, message)

	async def on_command_specific(self, room, message, command, nick, argstr):
		if similar(nick, room.session.nick):
			await self.module.on_command_specific(room, message, command, nick, argstr, True)

			if not argstr:
				await self.botrulez_ping(room, message, command)
				await self.botrulez_help(room, message, command, text=self.module.LONG_HELP)
				await self.botrulez_uptime(room, message, command)
				await self.botrulez_kill(room, message, command)
				await self.botrulez_restart(room, message, command)

		else:
			await self.module.on_command_specific(room, message, command, nick, argstr, False)

	async def on_command_general(self, room, message, command, argstr):
		await self.module.on_command_general(room, message, command, argstr)

		if not argstr:
			await self.botrulez_ping(room, message, command)
			await self.botrulez_help(room, message, command, text=self.module.SHORT_HELP)
