import json
import time
import threading
import websocket
from websocket import WebSocketException as WSException


ROOM_FORMAT = "wss://euphoria.io/room/{}/ws"


class Connection():
	"""
	Stays connected to a room in its own thread.
	Callback functions are called when a packet is received.
	"""
	
	def __init__(self, room):
		"""
		room - name of the room to connect to
		"""
		
		self.room = room
		
		self.stopping = False
		
		self.ws = None
		self.send_id = 0
		self.callbacks = {}
		self.id_callbacks = {}
	
	def connect(self, tries=-1, delay=10):
		"""
		_connect(tries, delay) -> bool
		
		tries - maximum number of retries
		        -1 -> retry indefinitely
		
		Returns True on success, False on failure.
		
		Connect to the room.
		"""
		
		while tries != 0:
			try:
				self.ws = websocket.create_connection(
					ROOM_FORMAT.format(self.room),
					enable_multithread=True
				)
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
		
		if self.ws:
			self.ws.close()
			self.ws = None
	
	def launch(self):
		"""
		launch() -> Thread
		
		Connect to the room and spawn a new thread running run.
		"""
		
		if self.connect(tries=1):
			self.thread = threading.Thread(target=self.run, name=self.room)
			self.thread.start()
			return self.thread
		else:
			self.stop()
	
	def run(self):
		"""
		run() -> None
		
		Receive messages.
		"""
		
		while not self.stopping:
			try:
				self.handle_json(self.ws.recv())
			except (WSException, OSError, ValueError):
				if not self.stopping:
					self.disconnect()
					self.connect()
	
	def stop(self):
		"""
		stop() -> None
		
		Close the connection to the room.
		"""
		
		self.stopping = True
		self.disconnect()
	
	def join(self):
		"""
		join() -> None
		
		Join the thread spawned by launch.
		"""
		
		if self.thread:
			self.thread.join()
	
	def add_callback(self, ptype, callback, *args, **kwargs):
		"""
		add_callback(ptype, callback) -> None
		
		Add a function to be called when a packet of type ptype is received.
		"""
		
		if not ptype in self.callbacks:
			self.callbacks[ptype] = []
		
		callback_info = {
			"callback": callback,
			"args": args,
			"kwargs": kwargs
		}
		
		self.callbacks[ptype].append(callback_info)
	
	def add_id_callback(self, pid, callback, *args, **kwargs):
		"""
		add_id_callback(pid, callback) -> None
		
		Add a function to be called when a packet with id pid is received.
		"""
		
		if not pid in self.id_callbacks:
			self.id_callbacks[pid] = []
		
		callback_info = {
			"callback": callback,
			"args": args,
			"kwargs": kwargs
		}
		
		self.id_callbacks[pid].append(callback_info)
	
	def call_callback(self, event, *args):
		"""
		call_callback(event) -> None
		
		Call all callbacks subscribed to the event with *args.
		"""
		
		if event in self.callbacks:
			for c_info in self.callbacks[event]:
				c = c_info["callback"]
				args = c_info["args"] + args
				kwargs = c_info["kwargs"]
				c(*args, **kwargs)
	
	def call_id_callback(self, pid, *args):
		"""
		call_callback(pid) -> None
		
		Call all callbacks subscribed to the pid with *args.
		"""
		
		if pid in self.id_callbacks:
			for c_info in self.id_callbacks.pop(pid):
				c = c_info["callback"]
				args = c_info["args"] + args
				kwargs = c_info["kwargs"]
				c(*args, **kwargs)
	
	def handle_json(self, data):
		"""
		handle_json(data) -> None
		
		Handle incoming 'raw' data.
		"""
		
		packet = json.loads(data)
		self.handle_packet(packet)
	
	def handle_packet(self, packet):
		"""
		handle_packet(ptype, data) -> None
		
		Handle incoming packets
		"""
		
		if "data" in packet:
			data = packet["data"]
		else:
			data = None
		
		self.call_callback(packet["type"], data)
		
		if "id" in packet:
			self.call_id_callback(packet["id"], data)
	
	def send_json(self, data):
		"""
		send_json(data) -> None
		
		Send 'raw' json.
		"""
		
		if self.ws:
			try:
				self.ws.send(json.dumps(data))
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
			"id": str(self.send_id)
		}
		self.send_id += 1
		self.send_json(packet)
