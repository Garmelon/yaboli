import json
import time
import threading
import websocket
from websocket import WebSocketException as WSException

from . import callbacks

class Connection():
	"""
	Stays connected to a room in its own thread.
	Callback functions are called when a packet is received.
	
	Callbacks:
		- all the message types from api.euphoria.io
		  These pass the packet data as argument to the called functions.
		  The other callbacks don't pass any special arguments.
		- "connect"
		- "disconnect"
		- "stop"
	"""
	
	ROOM_FORMAT = "wss://euphoria.io/room/{}/ws"
	
	def __init__(self, room, url_format=None):
		"""
		room - name of the room to connect to
		
		"""
		
		self.room = room
		
		if not url_format:
			url_format = self.ROOM_FORMAT
		self._url = url_format.format(self.room)
		
		self._stopping = False
		
		self._ws = None
		self._thread = None
		self._send_id = 0
		self._callbacks = callbacks.Callbacks()
		self._id_callbacks = callbacks.Callbacks()
	
	def _connect(self, tries=-1, delay=10):
		"""
		_connect(tries, delay) -> bool
		
		tries - maximum number of retries
		        -1 -> retry indefinitely
		
		Returns True on success, False on failure.
		
		Connect to the room.
		"""
		
		while tries != 0:
			try:
				self._ws = websocket.create_connection(
					self._url,
					enable_multithread=True
				)
				
				self._callbacks.call("connect")
				
				return True
			except WSException:
				if tries > 0:
					tries -= 1
				if tries != 0:
					time.sleep(delay)
		return False
	
	def disconnect(self):
		"""
		disconnect() -> None
		
		Reconnect to the room.
		WARNING: To completely disconnect, use stop().
		"""
		
		if self._ws:
			self._ws.close()
			self._ws = None
		
		self._callbacks.call("disconnect")
	
	def launch(self):
		"""
		launch() -> Thread
		
		Connect to the room and spawn a new thread running run.
		"""
		
		if self._connect(tries=1):
			self._thread = threading.Thread(target=self._run,
			                                name="{}-{}".format(self.room, int(time.time())))
			self._thread.start()
			return self._thread
		else:
			self.stop()
	
	def _run(self):
		"""
		_run() -> None
		
		Receive messages.
		"""
		
		while not self._stopping:
			try:
				self._handle_json(self._ws.recv())
			except (WSException, ConnectionResetError):
				if not self._stopping:
					self.disconnect()
					self._connect()
	
	def stop(self):
		"""
		stop() -> None
		
		Close the connection to the room.
		Joins the thread launched by self.launch().
		"""
		
		self._stopping = True
		self.disconnect()
		
		self._callbacks.call("stop")
		
		if self._thread and self._thread != threading.current_thread():
			self._thread.join()
	
	def next_id(self):
		"""
		next_id() -> id
		
		Returns the id that will be used for the next package.
		"""
		
		return str(self._send_id)
	
	def add_callback(self, ptype, callback, *args, **kwargs):
		"""
		add_callback(ptype, callback, *args, **kwargs) -> None
		
		Add a function to be called when a packet of type ptype is received.
		"""
		
		self._callbacks.add(ptype, callback, *args, **kwargs)
	
	def add_id_callback(self, pid, callback, *args, **kwargs):
		"""
		add_id_callback(pid, callback, *args, **kwargs) -> None
		
		Add a function to be called when a packet with id pid is received.
		"""
		
		self._id_callbacks.add(pid, callback, *args, **kwargs)
	
	def add_next_callback(self, callback, *args, **kwargs):
		"""
		add_next_callback(callback, *args, **kwargs) -> None
		
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
		
		if "data" in packet:
			data = packet["data"]
		else:
			data = None
		
		if "error" in packet:
			error = packet["error"]
		else:
			error = None
		
		self._callbacks.call(packet["type"], data, error)
		
		if "id" in packet:
			self._id_callbacks.call(packet["id"], data, error)
			self._id_callbacks.remove(packet["id"])
	
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
