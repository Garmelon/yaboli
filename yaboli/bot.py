# PLACEHOLDER BOT CLASS

class Bot:
	def __init__(self, name, room, pw=None, creator=None, create_room=None, create_time=None):
		self.name = name
		self.room = room
		self.pw   = pw
		self.creator     = creator
		self.create_room = create_room
		self.create_time = create_time
	
	def run(self, bot_id):
		pass
	
	def stop(self):
		pass
	
	def get_name(self):
		return self.name
	
	def get_roomname(self):
		return self.room
	
	def get_roompw(self):
		return self.pw
	
	def get_creator(self):
		return self.creator
	
	def get_create_room(self):
		return self.create_room
	
	def get_create_time(self):
		return self.create_time
	
	def save(self):
		return [1, 2, 3]
	
	def load(self, data):
		pass
