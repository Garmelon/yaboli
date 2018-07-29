import asyncio
import logging

import yaboli
from yaboli.utils import *
from join_rooms import join_rooms # List of rooms kept in separate file, which is .gitignore'd

# Turn all debugging on
asyncio.get_event_loop().set_debug(True)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("yaboli").setLevel(logging.DEBUG)


class ExampleBot(yaboli.Bot):
	async def send(self, room, message):
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

		if message.content == "!!!":
			await room._connection._ws.close()
	
	forward = send # should work without modifications for most bots

def main():
	bot = ExampleBot("ExampleBot", "examplebot.cookie")
	join_rooms(bot)
	asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
	main()
