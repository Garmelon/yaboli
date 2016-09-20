class Mention(str):
	"""
	A class to compare @mentions to nicks and other @mentions
	"""
	
	def mentionable(nick):
		"""
		A mentionable version of the nick.
		Add an "@" in front to mention someone on euphoria.
		"""
		
		# return "".join(c for c in nick if not c in ".!?;&<'\"" and not c.isspace())
		return "".join(filter(lambda c: c not in ".!?;&<'\"" and not c.isspace(), nick))
	
	def __new__(cls, nick):
		return str.__new__(cls, Mention.mentionable(nick))
	
	def __add__(self, other):
		return Mention(str(self) + other)
	
	def __mod__(self, other):
		return Mention(str(self) % other)
	
	def __mul__(self, other):
		return Mention(str(self)*other)
	
	def __repr__(self):
		return "@" + super().__repr__()
	
	def __radd__(self, other):
		return Mention(other + str(self))
	
	def __rmul__(self, other):
		return Mention(other*str(self))
	
	def format(self, *args, **kwargs):
		return Mention(str(self).format(*args, **kwargs))
	
	def format_map(self, *args, **kwargs):
		return Mention(str(self).format_map(*args, **kwargs))
	
	def replace(self, *args, **kwargs):
		return Mention(str(self).replace(*args, **kwargs))
