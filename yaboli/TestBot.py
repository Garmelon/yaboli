import asyncio
from controller import Bot



class TestBot(Bot):
	def __init__(self):
		pass
	
	async def on_connected(self):
		await self.room.set_nick("TestBot")

if __name__ == "__main__":
	bot = TestBot()
	asyncio.get_event_loop().run_until_complete(bot.run())
