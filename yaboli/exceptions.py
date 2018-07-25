__all__ = ["ConnectionClosed"]

class ConnectionClosed(Exception):
	pass

class RoomException(Exception):
	pass

class AuthenticationRequired(RoomException):
	pass

class RoomClosed(RoomException):
	pass
