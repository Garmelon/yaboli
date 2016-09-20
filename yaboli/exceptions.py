class YaboliException(Exception):
	"""
	Generic yaboli exception class.
	"""
	pass

class CreateBotException(YaboliException):
	"""
	Raised when a bot could not be created.
	"""
	pass
