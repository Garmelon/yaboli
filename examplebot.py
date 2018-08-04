import asyncio
import configparser
import logging

import yaboli
from yaboli.utils import *

# Turn all debugging on
asyncio.get_event_loop().set_debug(True)
#logging.getLogger("asyncio").setLevel(logging.INFO)
#logging.getLogger("yaboli").setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


class ExampleBot(yaboli.Bot):
	async def on_command_specific(self, room, message, command, nick, argstr):
		long_help = (
			"I'm an example bot for the yaboli bot library,"
			" which can be found at https://github.com/Garmelon/yaboli"
		)

		if similar(nick, room.session.nick) and not argstr:
			await self.botrulez_ping(room, message, command, text="ExamplePong!")
			await self.botrulez_help(room, message, command, text=long_help)
			await self.botrulez_uptime(room, message, command)
			await self.botrulez_kill(room, message, command)
			await self.botrulez_restart(room, message, command)

	async def on_command_general(self, room, message, command, argstr):
		short_help = "Example bot for the yaboli bot library"

		if not argstr:
			await self.botrulez_ping(room, message, command, text="ExamplePong!")
			await self.botrulez_help(room, message, command, text=short_help)

def main(configfile):
	config = configparser.ConfigParser(allow_no_value=True)
	config.read(configfile)

	nick = config.get("general", "nick")
	cookiefile = config.get("general", "cookiefile", fallback=None)
	bot = ExampleBot(nick, cookiefile=cookiefile)

	for room, password in config.items("rooms"):
		if not password:
			password = None
		bot.join_room(room, password=password)

	asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
	main("examplebot.conf")
