import json
import logging
import ssl
import time
import threading
import websocket
from websocket import WebSocketException as WSException

from .callbacks import Callbacks

SSLOPT = {"ca_certs": ssl.get_default_verify_paths().cafile}
#SSLOPT = {"cert_reqs": ssl.CERT_NONE}
ROOM_FORMAT = "wss://euphoria.io/room/{}/ws"
logger = logging.getLogger(__name__)

class Connection():
	"""
	Stays connected to a room in its own thread.
	Callback functions are called when a packet is received.
	
	Callbacks:
		- all the message types from api.euphoria.io
		  These pass the packet data and errors (if any) as arguments to the called functions.
		  The other callbacks don't pass any special arguments.
		- "connect"
		- "disconnect"
		- "stop"
	"""
	
	def __init__(self, room, url_format=None):
		"""
		room        - name of the room to connect to
		url_format  - url the bot will connect to, where the room name is represented by {}
		"""
		
		self.room = room
		
		self._url_format = url_format or ROOM_FORMAT
		
		self._stopping = False
		
		self._ws = None
		self._thread = None
		self._send_id = 0
		self._callbacks = Callbacks()
		self._id_callbacks = Callbacks()
		self._lock = threading.RLock()
	
	def __enter__(self):
		self._lock.acquire()
		return self
	
	def __exit__(self, exc_type, exc_value, traceback):
		self._lock.release()
	
	def _connect(self, tries=20, delay=10):
		"""
		_connect(tries, delay) -> bool
		
		delay  - delay between retries (in seconds)
		tries  - maximum number of retries
		         -1 -> retry indefinitely
		
		Returns True on success, False on failure.
		
		Connect to the room.
		"""
		
		while tries != 0:
			try:
				url = self._url_format.format(self.room)
				logger.info("Connecting to url: {!r} ({} {} left)".format(
					url,
					tries-1 if tries > 0 else "infinite",
					"tries" if (tries-1) != 1 else "try" # proper english :D
				))
				self._ws = websocket.create_connection(
					url,
					enable_multithread=True,
					sslopt=SSLOPT
				)
			
			except WSException:
				if tries > 0:
					tries -= 1
				if tries != 0:
					logger.info("Connection failed. Retrying in {} seconds.".format(delay))
					time.sleep(delay)
				else:
					logger.info("No more tries, stopping.")
					self.stop()
			
			else:
				logger.debug("Connected")
				self._callbacks.call("connect")
				return True
				
		return False
	
	def disconnect(self):
		"""
		disconnect() -> None
		
		Disconnect from the room.
		This will cause the connection to reconnect.
		To completely disconnect, use stop().
		"""
		
		if self._ws:
			logger.debug("Closing connection!")
			self._ws.abort()
			self._ws.close()
			self._ws = None
		
		logger.debug("Disconnected")
		self._callbacks.call("disconnect")
	
	def launch(self):
		"""
		launch() -> Thread
		
		Connect to the room and spawn a new thread.
		"""
		
		self._stopping = False
		self._thread = threading.Thread(
			target=self._run,
			name="{}-{}".format(int(time.time()), self.room)
		)
		logger.debug("Launching new thread: {}".format(self._thread.name))
		self._thread.start()
		return self._thread
	
	def _run(self):
		"""
		_run() -> None
		
		Receive messages.
		"""
		
		logger.debug("Running")
		
		if not self.switch_to(self.room):
			return
		
		while not self._stopping:
			try:
				j = self._ws.recv()
				self._handle_json(j)
			except (WSException, ConnectionResetError):
				if not self._stopping:
					self.disconnect()
					self._connect()
		
		logger.debug("Finished running")
	
	def stop(self):
		"""
		stop() -> None
		
		Close the connection to the room.
		Joins the thread launched by self.launch().
		"""
		
		logger.debug("Stopping")
		self._stopping = True
		self.disconnect()
		
		self._callbacks.call("stop")
		
		if self._thread and self._thread != threading.current_thread():
			self._thread.join()
	
	def switch_to(self, new_room):
		"""
		switch_to(new_room) -> bool
		
		Returns True on success, False on failure.
		
		Attempts to connect to new_room.
		"""
		
		old_room = self.room if self._ws else None
		self.room = new_room
		self.disconnect()
		if old_room:
			logger.info("Switching to &{} from &{}.".format(old_room, new_room))
		else:
			logger.info("Switching to &{}.".format(new_room))
		
		if not self._connect(tries=1):
			if old_room:
				logger.info("Could not connect to &{}: Connecting to ${} again.".format(new_room, old_room))
				self.room = old_room
				self._connect()
			else:
				logger.info("Could not connect to &{}.".format(new_room))
			
			return False
		
		return True
	
	def next_id(self):
		"""
		next_id() -> id
		
		Returns the id that will be used for the next package.
		"""
		
		return str(self._send_id)
	
	def subscribe(self, ptype, callback, *args, **kwargs):
		"""
		subscribe(ptype, callback, *args, **kwargs) -> None
		
		Add a function to be called when a packet of type ptype is received.
		"""
		
		self._callbacks.add(ptype, callback, *args, **kwargs)
	
	def subscribe_to_id(self, pid, callback, *args, **kwargs):
		"""
		subscribe_to_id(pid, callback, *args, **kwargs) -> None
		
		Add a function to be called when a packet with id pid is received.
		"""
		
		self._id_callbacks.add(pid, callback, *args, **kwargs)
	
	def subscribe_to_next(self, callback, *args, **kwargs):
		"""
		subscribe_to_next(callback, *args, **kwargs) -> None
		
		Add a function to be called when the answer to the next message sent is received.
		"""
		
		self._id_callbacks.add(self.next_id(), callback, *args, **kwargs)
	
	def _handle_json(self, data):
		"""
		handle_json(data) -> None
		
		Handle incoming 'raw' data.
		"""
		
		packet = json.loads(data)
		self._handle_packet(packet)
	
	def _handle_packet(self, packet):
		"""
		_handle_packet(ptype, data) -> None
		
		Handle incoming packets
		"""
		
		ptype = packet.get("type")
		logger.debug("Handling packet of type {}.".format(ptype))
		
		data = packet.get("data")
		if "error" in packet:
			logger.debug("Error in packet: {!r}".format(error))
		
		if "id" in packet:
			self._id_callbacks.call(packet["id"], data, packet)
			self._id_callbacks.remove(packet["id"])
		
		self._callbacks.call(packet["type"], data, packet)
	
	def _send_json(self, data):
		"""
		_send_json(data) -> None
		
		Send 'raw' json.
		"""
		
		if self._ws:
			try:
				self._ws.send(json.dumps(data))
			except WSException:
				self.disconnect()
	
	def send_packet(self, ptype, **kwargs):
		"""
		send_packet(ptype, **kwargs) -> None
		
		Send a formatted packet.
		"""
		
		packet = {
			"type": ptype,
			"data": kwargs or None,
			"id": str(self._send_id)
		}
		self._send_id += 1
		self._send_json(packet)
