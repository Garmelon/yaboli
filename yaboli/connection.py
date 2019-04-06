__all__ = ["Connection"]

class Connection:
    """
    The Connection handles the lower-level stuff required when connecting to
    euphoria, such as:

    - Creating a websocket connection
    - Encoding and decoding packets (json)
    - Waiting for the server's asynchronous replies to packets
    - Keeping the connection alive (ping, ping-reply packets)
    - Reconnecting (timeout while connecting, no pings received in some time)



    Life cycle of a Connection:

    1. create connection and register event callbacks
    2. call connect()
    3. send and receive packets, reconnecting automatically when connection is
    lost
    4. call disconnect(), return to 2.


    IN PHASE 1, parameters such as the url the Connection should connect to are
    set. Usually, event callbacks are also registered in this phase.


    IN PHASE 2, the Connection attempts to connect to the url set in phase 1.
    If successfully connected, it fires a "connected" event.


    IN PHASE 3, the Connection listenes for packets from the server and fires
    the corresponding events. Packets can be sent using the Connection.

    If the Connection has to reconnect for some reason, it first fires a
    "reconnecting" event. Then it tries to reconnect until it has established a
    connection to euphoria again. After the connection is reestablished, it
    fires a "reconnected" event.


    IN PHASE 4, the Connection fires a "disconnecting" event and then closes
    the connection to euphoria. This event is the last event that is fired
    until connect() is called again.



    Events:

    - "connected" : No arguments
    - "reconnecting" : No arguments
    - "reconnected" : No arguments
    - "disconnecting" : No arguments
    - "on_<euph event name>": the packet, parsed as JSON

    Events ending with "-ing" ("reconnecting", "disconnecting") are fired at
    the beginning of the process they represent. Events ending with "-ed"
    ("connected", "reconnected") are fired after the process they represent has
    completed.

    Examples for the last category of events include "on_message-event",
    "on_part-event" and "on_ping".
    """

    def __init__(self,
            url: str):
        self._url = url
