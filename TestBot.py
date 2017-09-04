import asyncio
import yaboli
from yaboli.utils import *



#class TestBot(Bot):
class TestBot(yaboli.Controller):
	def __init__(self, nick):
		super().__init__(nick=nick)
	
	async def on_send(self, message):
		if message.content == "!spawnevil":
			bot = TestBot("TestSpawn")
			task, reason = await bot.connect("test")
			second = await self.room.send("We have " + ("a" if task else "no") + " task. Reason: " + reason, message.message_id)
			if task:
				await bot.stop()
				await self.room.send("Stopped." if task.done() else "Still running (!)", second.message_id)
		
			await self.room.send("All's over now.", message.message_id)
		
		elif message.content == "!tree":
			messages = [message]
			newmessages = []
			for i in range(2):
				for m in messages:
					for j in range(2):
						newm = await self.room.send(f"{m.content}.{j}", m.message_id)
						newmessages.append(newm)
				messages = newmessages
				newmessages = []

async def run_bot():
	bot = TestBot("TestSummoner")
	task, reason = await bot.connect("test")
	if task:
		await task

if __name__ == "__main__":
	asyncio.get_event_loop().run_until_complete(run_bot())
