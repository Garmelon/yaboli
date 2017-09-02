import asyncio
#from controller import Bot
from controller import Controller
from utils import *



#class TestBot(Bot):
class TestBot(Controller):
	def __init__(self, roomname):
		super().__init__(roomname)
	
	async def on_snapshot(self, user_id, session_id, version, listing, log, nick=None,
	                      pm_with_nick=None, pm_with_user_id=None):
		await self.room.nick("TestBot")
	
	async def on_send(self, message):
		await self.room.send("Hey, a message!", message.message_id)
	
	async def on_join(self, session):
		if session.nick != "":
			await self.room.send(f"Hey, a @{mention(session.nick)}!")
		else:
			await self.room.send("Hey, a lurker!")
	
	async def on_nick(self, session_id, user_id, from_nick, to_nick):
		if from_nick != "" and to_nick != "":
			if from_nick == to_nick:
				await self.room.send(f"You didn't even change your nick, @{mention(to_nick)} :(")
			else:
				await self.room.send(f"Bye @{mention(from_nick)}, hi @{mention(to_nick)}")
		elif from_nick != "":
			await self.room.send(f"Bye @{mention(from_nick)}? This message should never appear...")
		elif to_nick != "":
			await self.room.send(f"Hey, a @{mention(to_nick)}!")
		else:
			await self.room.send("I have no idea how you did that. This message should never appear...")
	
	async def on_part(self, session):
		if session.nick != "":
			await self.room.send(f"Bye, you @{mention(session.nick)}!")
		else:
			await self.room.send("Bye, you lurker!")

if __name__ == "__main__":
	bot = TestBot("test")
	asyncio.get_event_loop().run_until_complete(bot.run())
