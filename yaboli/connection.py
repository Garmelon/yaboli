import logging
logger = logging.getLogger(__name__)

import asyncio
asyncio.get_event_loop().set_debug(True)

import json
import websockets
import socket
#from websockets import ConnectionClosed

__all__ = ["Connection"]



class Connection:
	def __init__(self, url, packet_hook, cookie=None, ping_timeout=10, ping_delay=30):
		self.url = url
		self.packet_hook = packet_hook
		self.cookie = cookie
		self.ping_timeout = ping_timeout # how long to wait for websocket ping reply
		self.ping_delay = ping_delay # how long to wait between pings
		
		self._ws = None
		self._pid = 0 # successive packet ids
		self._spawned_tasks = set()
		self._pending_responses = {}
		
		self._runtask = None
		self._pingtask = None # pings 
	
	async def connect(self, max_tries=10, delay=60):
		"""
		success = await connect(max_tries=10, delay=60)
		
		Attempt to connect to a room.
		Returns the task listening for packets, or None if the attempt failed.
		"""
		
		logger.debug(f"Attempting to connect, max_tries={max_tries}")
		
		await self.stop()
		
		logger.debug(f"Stopped previously running things.")
		
		tries_left = max_tries
		while tries_left > 0:
			logger.info(f"Attempting to connect, {tries_left} tries left.")
			tries_left -= 1
			try:
				self._ws = await websockets.connect(self.url, max_size=None)
			except (websockets.InvalidURI, websockets.InvalidHandshake, socket.gaierror):
				self._ws = None
				if tries_left > 0:
					await asyncio.sleep(delay)
			else:
				self._runtask = asyncio.ensure_future(self._run())
				self._pingtask = asyncio.ensure_future(self._ping())
				logger.debug(f"return self._runtask")
				return self._runtask
	
	async def _run(self):
		"""
		Listen for packets and deal with them accordingly.
		"""
		
		try:
			while True:
				await self._handle_next_message()
		except websockets.ConnectionClosed:
			pass
		finally:
			self._clean_up_futures()
			self._clean_up_tasks()
			
			await self._ws.close() # just to make sure
			await self._pingtask # should stop now that the ws is closed
			self._ws = None
	
	async def _ping(self):
		"""
		Periodically ping the server to detect a timeout.
		"""
		
		while True:
			try:
				logger.debug("Pinging...")
				wait_for_reply = await self._ws.ping()
				await asyncio.wait_for(wait_for_reply, self.ping_timeout)
				logger.debug("Pinged!")
			except asyncio.TimeoutError:
				logger.warning("Ping timed out.")
				await self._ws.close2()
				break
			except websockets.ConnectionClosed:
				break
			else:
				await asyncio.sleep(self.ping_delay)
	
	async def stop(self):
		"""
		Close websocket connection and wait for running task to stop.
		"""
		
		if self._ws:
			await self._ws.close()
		
		if self._runtask:
			await self._runtask
	
	async def send(self, ptype, data=None, await_response=True):
		if not self._ws:
			raise asyncio.CancelledError
		
		pid = str(self._new_pid())
		packet = {
			"type": ptype,
			"id": pid
		}
		if data:
			packet["data"] = data
		
		if await_response:
			wait_for = self._wait_for_response(pid)
		
		logging.debug(f"Currently used websocket at self._ws: {self._ws}")
		await self._ws.send(json.dumps(packet, separators=(',', ':'))) # minimum size
		
		if await_response:
			await wait_for
			return wait_for.result()
	
	def _new_pid(self):
		self._pid += 1
		return self._pid
	
	async def _handle_next_message(self):
		response = await self._ws.recv()
		task = asyncio.ensure_future(self._handle_json(response))
		self._track_task(task) # will be cancelled when the connection is closed
	
	def _clean_up_futures(self):
		for pid, future in self._pending_responses.items():
			logger.debug(f"Cancelling future: {future}")
			future.cancel()
		self._pending_responses = {}
	
	def _clean_up_tasks(self):
		for task in self._spawned_tasks:
			if not task.done():
				logger.debug(f"Cancelling task: {task}")
				task.cancel()
			else:
				logger.debug(f"Task already done: {task}")
				logger.debug(f"Exception: {task.exception()}")
		self._spawned_tasks = set()
	
	async def _handle_json(self, text):
		packet = json.loads(text)
		
		# Deal with pending responses
		pid = packet.get("id", None)
		future = self._pending_responses.pop(pid, None)
		if future:
			future.set_result(packet)
		
		# Pass packet onto room
		await self.packet_hook(packet)
	
	def _track_task(self, task):
		self._spawned_tasks.add(task)
		
		# only keep running tasks
		#tasks = set()
		#for task in self._spawned_tasks:
			#if not task.done():
				#logger.debug(f"Keeping task: {task}")
				#tasks.add(task)
			#else:
				#logger.debug(f"Deleting task: {task}")
		#self._spawned_tasks = tasks
		self._spawned_tasks = {task for task in self._spawned_tasks if not task.done()} # TODO: Reenable
	
	def _wait_for_response(self, pid):
		future = asyncio.Future()
		self._pending_responses[pid] = future
		
		return future
