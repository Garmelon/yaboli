class YaboliException(Exception):
	"""
	Generic yaboli exception class.
	"""
	
	pass

class BotManagerException(YaboliException):
	"""
	Generic BotManager exception class.
	"""
	
	pass

class CreateBotException(BotManagerException):
	"""
	This exception will be raised when BotManager could not create a bot.
	"""
	
	pass

class BotNotFoundException(BotManagerException):
	"""
	This exception will be raised when BotManager could not find a bot.
	"""
	
	pass

class BotException(YaboliException):
	"""
	Generic Bot exception class.
	"""
	
	pass

class ParseMessageException(BotException):
	"""
	This exception will be raised when a failure parsing a message occurs.
	"""
	
	pass
