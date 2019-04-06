__all__ = ["EuphException", "JoinException", "CouldNotConnectException",
        "CouldNotAuthenticateException", "RoomClosedException",
        "RateLimitException", "NotLoggedInException", "UnauthorizedException"]

class EuphException(Exception):
    pass

# Joining a room

class JoinException(EuphException):
    """
    An exception that happened while joining a room.
    """
    pass

class CouldNotConnectException(JoinException):
    """
    Could not establish a websocket connection to euphoria.
    """
    pass

class CouldNotAuthenticateException(JoinException):
    """
    The password is either incorrect or not set, even though authentication is
    required.
    """
    pass

# Doing stuff in a room

class RoomClosedException(EuphException):
    """
    The room has been closed already.

    This means that phase 4 (see the docstring of Room) has been initiated or
    completed.
    """
    pass

# exception for having no username?

# Maybe these will become real exceptions one day?

class RateLimitException(EuphException):
    pass

class NotLoggedInException(EuphException):
    pass

class UnauthorizedException(EuphException):
    pass
