import asyncio
import yaboli

class ExampleBot(yaboli.Bot):
	async def send(self, room, message):
		ping = "ExamplePong!"
		short_help = "Example bot for the yaboli bot library"
		long_help = "I'm an example bot for the yaboli bot library, which can be found at https://github.com/Garmelon/yaboli"

		await self.botrulez_ping_general(room, message, ping_text=ping)
		await self.botrulez_ping_specific(room, message, ping_text=ping)
		await self.botrulez_help_general(room, message, help_text=short_help)
		await self.botrulez_help_specific(room, message, help_text=long_help)
		await self.botrulez_uptime(room, message)
		await self.botrulez_kill(room, message)
		await self.botrulez_restart(room, message)
	
	forward = send # should work without modifications for most bots

bot = ExampleBot("ExampleBot", "examplebot_cookies", rooms=["test", "welcome"])
asyncio.get_event_loop().run_forever()
