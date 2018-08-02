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
	async def on_send(self, room, message):
		ping = "ExamplePong!"
		short_help = "Example bot for the yaboli bot library"
		long_help = (
			"I'm an example bot for the yaboli bot library,"
			" which can be found at https://github.com/Garmelon/yaboli"
		)

		await self.botrulez_ping_general(room, message, text=ping)
		await self.botrulez_ping_specific(room, message, text=ping)
		await self.botrulez_help_general(room, message, text=short_help)
		await self.botrulez_help_specific(room, message, text=long_help)
		await self.botrulez_uptime(room, message)
		await self.botrulez_kill(room, message, text="/me dies spectacularly")
		await self.botrulez_restart(room, message, text="/me restarts spectacularly")

def main(configfile):
	config = configparser.ConfigParser(allow_no_value=True)
	config.read(configfile)

	nick = config.get("general", "nick")
	cookiefile = config.get("general", "cookiefile", fallback=None)
	print(cookiefile)
	bot = ExampleBot(nick, cookiefile=cookiefile)

	for room, password in config.items("rooms"):
		if not password:
			password = None
		bot.join_room(room, password=password)

	asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
	main("examplebot.conf")
