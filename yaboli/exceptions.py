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
        "RoomNotConnectedException",
        "EuphError",
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

class RoomNotConnectedException(EuphException):
    """
    Either the Room's connect() function has not been called or it has not
    completed successfully.
    """
    pass

class EuphError(EuphException):
    """
    The euphoria server has sent back an "error" field in its response.
    """
    pass
