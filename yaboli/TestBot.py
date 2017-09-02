import asyncio
#from controller import Bot
from controller import Controller



#class TestBot(Bot):
class TestBot(Controller):
	def __init__(self, roomname):
		super().__init__(roomname)
	
	#async def on_connected(self):
		#await self.room.set_nick("TestBot")
		
	async def on_hello(self, user_id, session, room_is_private, version, account=None,
	                   account_has_access=None, account_email_verified=None):
		print(repr(session.user_id), repr(session.session_id), repr(session.name))

if __name__ == "__main__":
	bot = TestBot("test")
	asyncio.get_event_loop().run_until_complete(bot.run())
