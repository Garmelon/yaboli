"""
Copy this template script and modify it to create a new bot.
"""

import yaboli
from yaboli.utils import *
import sys



class YourBot(yaboli.Bot):
	"""
	Your bot's docstring
	"""
	
	def __init__(self):
		super().__init__("Your bot's name")
		
		# set help and other settings here
		#self.help_general = None
		#self.help_specific = "No help available"
		#self.killable = True
		#self.kill_message = "/me *poof*"
		#self.restartable = True
		#self.restart_message = "/me temporary *poof*"
	
	# Event callbacks - just fill in your code.
	# If the function contains a super(), DON'T remove it unless you know what you're doing!
	# (You can remove the function itself though.)
	# When you're done, remove all unneeded functions.
	
	async def on_connected(self):
		await super().on_connected()
	
	async def on_disconnected(self):
		await super().on_disconnected()
	
	async def on_bounce(self, reason=None, auth_options=[], agent_id=None, ip=None):
		await super().on_bounce(reason, auth_options, agent_id, ip)
	
	async def on_disconnect(self, reason):
		pass
	
	async def on_hello(self, user_id, session, room_is_private, version, account=None,
	                   account_has_access=None, account_email_verified=None):
		pass
	
	async def on_join(self, session):
		pass
	
	async def on_login(self, account_id):
		pass
	
	async def on_logout(self):
		pass
	
	async def on_network(self, ntype, server_id, server_era):
		pass
	
	async def on_nick(self, session_id, user_id, from_nick, to_nick):
		pass
	
	async def on_edit_message(self, edit_id, message):
		pass
	
	async def on_part(self, session):
		pass
	
	async def on_ping(self, ptime, pnext):
		await super().on_ping(ptime, pnext)
	
	async def on_pm_initiate(self, from_id, from_nick, from_room, pm_id):
		pass
	
	async def on_send(self, message):
		await super().on_send(message) # This is where yaboli.bot reacts to commands
	
	async def on_snapshot(self, user_id, session_id, version, listing, log, nick=None,
	                      pm_with_nick=None, pm_with_user_id=None):
		await super().on_snapshot(user_id, session_id, version, listing, log, nick, pm_with_nick,
		                    pm_with_user_id)

def main():
	if len(sys.argv) == 2:
		run_bot(YourBot, sys.argv[1])
	else:
		print("USAGE:")
		print(f"  {sys.argv[0]} <room>")
		return

if __name__ == "__main__":
	main()
