import yaboli
from yaboli.utils import *



#class TestBot(Bot):
class TestBot(yaboli.Bot):
	def __init__(self, nick):
		super().__init__(nick=nick)
		
		self.register_callback("tree", self.command_tree, specific=False)
	
	#async def on_send(self, message):
		#if message.content == "!spawnevil":
			#bot = TestBot("TestSpawn")
			#task, reason = await bot.connect("test")
			#second = await self.room.send("We have " + ("a" if task else "no") + " task. Reason: " + reason, message.message_id)
			#if task:
				#await bot.stop()
				#await self.room.send("Stopped." if task.done() else "Still running (!)", second.message_id)
		
			#await self.room.send("All's over now.", message.message_id)
		
		#elif message.content == "!tree":
			#messages = [message]
			#newmessages = []
			#for i in range(2):
				#for m in messages:
					#for j in range(2):
						#newm = await self.room.send(f"{m.content}.{j}", m.message_id)
						#newmessages.append(newm)
				#messages = newmessages
				#newmessages = []
	
	async def command_tree(self, message, args):
		messages = [message]
		newmessages = []
		for i in range(2):
			for m in messages:
				for j in range(2):
					newm = await self.room.send(f"{message.content}.{j}", m.message_id)
					newmessages.append(newm)
			messages = newmessages
			newmessages = []

if __name__ == "__main__":
	bot = TestBot("TestSummoner")
	run_controller(bot, "test")
