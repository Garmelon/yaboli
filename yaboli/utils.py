import asyncio
#import logging
import time

#logger = logging.getLogger(__name__)
__all__ = [
	#"run_controller", "run_bot",
	"mention", "mention_reduced", "similar",
	"format_time", "format_time_delta",
	"Session", "Listing",
	"Message", "Log",
]



#def run_controller(controller, room):
#	"""
#	Helper function to run a singular controller.
#	"""
#	
#	async def run():
#		task, reason = await controller.connect(room)
#		if task:
#			await task
#		else:
#			logger.warn(f"Could not connect to &{room}: {reason!r}")
#	
#	asyncio.get_event_loop().run_until_complete(run())
#
#def run_bot(bot_class, room, *args, **kwargs):
#	"""
#	Helper function to run a bot. To run Multibots, use the MultibotKeeper.
#	This restarts the bot when it is explicitly restarted through Bot.restart().
#	"""
#	
#	async def run():
#		while True:
#			logger.info(f"Creating new instance and connecting to &{room}")
#			bot = bot_class(*args, **kwargs)
#			task, reason = await bot.connect(room)
#			if task:
#				await task
#			else:
#				logger.warn(f"Could not connect to &{room}: {reason!r}")
#			
#			if bot.restarting:
#				logger.info(f"Restarting in &{room}")
#			else:
#				break
#	
#	asyncio.get_event_loop().run_until_complete(run())

def mention(nick):
	return "".join(c for c in nick if c not in ".!?;&<'\"" and not c.isspace())

def mention_reduced(nick):
	return mention(nick).lower()

def similar(nick1, nick2):
	return mention_reduced(nick1) == mention_reduced(nick2)

def format_time(timestamp):
	return time.strftime(
		"%Y-%m-%d %H:%M:%S UTC",
		time.gmtime(timestamp)
	)

def format_time_delta(delta):
	if delta < 0:
		result = "-"
	else:
		result = ""
	
	delta = int(delta)
	
	second = 1
	minute = second*60
	hour = minute*60
	day = hour*24
	
	if delta >= day:
		result += f"{delta//day}d "
		delta = delta%day
	
	if delta >= hour:
		result += f"{delta//hour}h "
		delta = delta%hour
	
	if delta >= minute:
		result += f"{delta//minute}m "
		delta = delta%minute
	
	result += f"{delta}s"
	
	return result

class Session:
	def __init__(self, user_id, nick, server_id, server_era, session_id, is_staff=None,
	             is_manager=None, client_address=None, real_address=None):
		self.user_id = user_id
		self.nick = nick
		self.server_id = server_id
		self.server_era = server_era
		self.session_id = session_id
		self.is_staff = is_staff
		self.is_manager = is_manager
		self.client_address = client_address
		self.real_address = real_address
	
	@property
	def uid(self):
		return self.user_id
	
	@uid.setter
	def uid(self, new_uid):
		self.user_id = new_uid
	
	@property
	def sid(self):
		return self.session_id
	
	@sid.setter
	def sid(self, new_sid):
		self.session_id = new_sid
	
	@classmethod
	def from_dict(cls, d):
		return cls(
			d.get("id"),
			d.get("name"),
			d.get("server_id"),
			d.get("server_era"),
			d.get("session_id"),
			d.get("is_staff", None),
			d.get("is_manager", None),
			d.get("client_address", None),
			d.get("real_address", None)
		)
	
	@property
	def client_type(self):
		# account, agent or bot
		return self.user_id.split(":")[0]

class Listing:
	def __init__(self):
		self._sessions = {}
	
	def __len__(self):
		return len(self._sessions)
	
	def add(self, session):
		self._sessions[session.session_id] = session
	
	def remove(self, session_id):
		self._sessions.pop(session_id)
	
	def remove_combo(self, server_id, server_era):
		removed = [ses for ses in self._sessions.items()
		           if ses.server_id == server_id and ses.server_era == server_era]

		self._sessions = {i: ses for i, ses in self._sessions.items()
		                  if ses.server_id != server_id and ses.server_era != server_era}

		return removed
	
	def by_sid(self, session_id):
		return self._sessions.get(session_id);
	
	def by_uid(self, user_id):
		return [ses for ses in self._sessions if ses.user_id == user_id]
	
	def get(self, types=["agent", "account", "bot"], lurker=None):
		sessions = []
		for uid, ses in self._sessions.items():
			if ses.client_type not in types:
				continue
			
			is_lurker = not ses.nick # "" or None
			if lurker is None or lurker == is_lurker:
				sessions.append(ses)
		
		return sessions
	
	#def get_people(self):
		#return self.get(types=["agent", "account"])
	
	#def get_accounts(self):
		#return self.get(types=["account"])
	
	#def get_agents(self):
		#return self.get(types=["agent"])
	
	#def get_bots(self):
		#return self.get(types=["bot"])

class Message():
	def __init__(self, message_id, time, sender, content, parent=None, previous_edit_id=None,
	             encryption_key=None, edited=None, deleted=None, truncated=None):
		self.message_id = message_id
		self.time = time
		self.sender = sender
		self.content = content
		self.parent = parent
		self.previous_edit_id = previous_edit_id
		self.encryption_key = encryption_key
		self.edited = edited
		self.deleted = deleted
		self.truncated = truncated
	
	@property
	def mid(self):
		return self.message_id
	
	@mid.setter
	def mid(self, new_mid):
		self.message_id = new_mid
	
	@classmethod
	def from_dict(cls, d):
		return cls(
			d.get("id"),
			d.get("time"),
			Session.from_dict(d.get("sender")),
			d.get("content"),
			d.get("parent", None),
			d.get("previous_edit_id", None),
			d.get("encryption_key", None),
			d.get("edited", None),
			d.get("deleted", None),
			d.get("truncated", None)
		)
