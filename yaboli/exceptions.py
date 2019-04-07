__all__ = [
        "EuphException",
        # Connection exceptions
        "IncorrectStateException",
        "ConnectionClosedException",
        # Joining a room
        "JoinException",
        "CouldNotConnectException",
        "CouldNotAuthenticateException",
        # Doing stuff in a room
        "RoomClosedException",
]

class EuphException(Exception):
    pass

# Connection exceptions

class IncorrectStateException(EuphException):
    """
    A Connection function was called while the Connection was in the incorrect
    state.
    """
    pass

class ConnectionClosedException(EuphException):
    """
    The connection was closed unexpectedly.
    """
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
