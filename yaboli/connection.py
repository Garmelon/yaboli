import asyncio
import json
import logging
import socket
import websockets

from .exceptions import *


logger = logging.getLogger(__name__)
__all__ = ["Connection"]


class Connection:
	def __init__(self, url, packet_callback, disconnect_callback, stop_callback, cookiejar=None, ping_timeout=10, ping_delay=30, reconnect_attempts=10):
		self.url = url
		self.packet_callback = packet_callback
		self.disconnect_callback = disconnect_callback
		self.stop_callback = stop_callback # is called when the connection stops on its own
		self.cookiejar = cookiejar
		self.ping_timeout = ping_timeout # how long to wait for websocket ping reply
		self.ping_delay = ping_delay # how long to wait between pings
		self.reconnect_attempts = reconnect_attempts

		self._ws = None
		self._pid = 0 # successive packet ids
		#self._spawned_tasks = set()
		self._pending_responses = {}

		self._stopped = False
		self._pingtask = None
		self._runtask = asyncio.ensure_future(self._run())
		# ... aaand the connection is started.

	async def send(self, ptype, data=None, await_response=True):
		if not self._ws:
			raise ConnectionClosed
			#raise asyncio.CancelledError

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
		try:
			await self._ws.send(json.dumps(packet, separators=(',', ':'))) # minimum size
		except websockets.ConnectionClosed:
			raise ConnectionClosed()

		if await_response:
			await wait_for
			return wait_for.result()

	async def stop(self):
		"""
		Close websocket connection and wait for running task to stop.

		No connection function are to be called after calling stop().
		This means that stop() can only be called once.
		"""

		if not self._stopped:
			self._stopped = True
			await self.reconnect() # _run() does the cleaning up now.
			await self._runtask

	async def reconnect(self):
		"""
		Reconnect to the url.
		"""

		if self._ws:
			await self._ws.close()

	async def _connect(self, tries, timeout=10):
		"""
		Attempt to connect to a room.
		If the Connection is already connected, it attempts to reconnect.

		Returns True on success, False on failure.

		If tries is None, connect retries infinitely.
		The delay between connection attempts doubles every attempt (starts with 1s).
		"""

		# Assumes _disconnect() has already been called in _run()

		delay = 1 # seconds
		while True:
			try:
				if self.cookiejar:
					cookies = [("Cookie", cookie) for cookie in self.cookiejar.sniff()]
					ws = asyncio.ensure_future(
						websockets.connect(self.url, max_size=None, extra_headers=cookies)
					)
				else:
					ws = asyncio.ensure_future(
						websockets.connect(self.url, max_size=None)
					)
				self._ws = await asyncio.wait_for(ws, timeout)
			except (websockets.InvalidHandshake, socket.gaierror, asyncio.TimeoutError): # not websockets.InvalidURI
				logger.warn(f"Connection attempt failed, {tries} tries left.")
				self._ws = None

				if tries is not None:
					tries -= 1
					if tries <= 0:
						logger.warn(f"{self.url}:Ran out of tries")
						return False

				await asyncio.sleep(delay)
				delay *= 2
			else:
				if self.cookiejar:
					for set_cookie in self._ws.response_headers.get_all("Set-Cookie"):
						self.cookiejar.bake(set_cookie)
						self.cookiejar.save()

				self._pingtask = asyncio.ensure_future(self._ping())

				return True

	async def _disconnect(self):
		"""
		Disconnect and clean up all "residue", such as:
		 - close existing websocket connection
		 - cancel all pending response futures with a ConnectionClosed exception
		 - reset package ID counter
		 - make sure the ping task has finished
		"""

		asyncio.ensure_future(self.disconnect_callback())

		# stop ping task
		if self._pingtask:
			self._pingtask.cancel()
			await self._pingtask
			self._pingtask = None

		if self._ws:
			await self._ws.close()
			self._ws = None

		self._pid = 0

		# clean up pending response futures
		for _, future in self._pending_responses.items():
			logger.debug(f"Cancelling future with ConnectionClosed: {future}")
			future.set_exception(ConnectionClosed("No server response"))
		self._pending_responses = {}

	async def _run(self):
		"""
		Listen for packets and deal with them accordingly.
		"""

		while not self._stopped:
			logger.debug(f"{self.url}:Connecting...")
			connected = await self._connect(self.reconnect_attempts)
			if connected:
				logger.debug(f"{self.url}:Connected")
				try:
					while True:
						await self._handle_next_message()
				except websockets.ConnectionClosed:
					pass
				finally:
					await self._disconnect() # disconnect and clean up
			else:
				logger.debug(f"{self.url}:Stopping")
				asyncio.ensure_future(self.stop_callback)
				self._stopped = True
				await self._disconnect()


	async def _ping(self):
		"""
		Periodically ping the server to detect a timeout.
		"""

		try:
			while True:
				logger.debug(f"{self.url}:Pinging...")
				wait_for_reply = await self._ws.ping()
				await asyncio.wait_for(wait_for_reply, self.ping_timeout)
				logger.debug(f"{self.url}:Pinged!")
				await asyncio.sleep(self.ping_delay)
		except asyncio.TimeoutError:
			logger.warning(f"{self.url}:Ping timed out")
			await self.reconnect()
		except (websockets.ConnectionClosed, ConnectionResetError, asyncio.CancelledError):
			pass

	def _new_pid(self):
		self._pid += 1
		return self._pid

	async def _handle_next_message(self):
		response = await self._ws.recv()
		packet = json.loads(response)

		ptype = packet.get("type")
		data = packet.get("data", None)
		error = packet.get("error", None)
		if packet.get("throttled", False):
			throttled = packet.get("throttled_reason")
		else:
			throttled = None

		# Deal with pending responses
		pid = packet.get("id", None)
		future = self._pending_responses.pop(pid, None)
		if future:
			future.set_result((ptype, data, error, throttled))

		# Pass packet onto room
		asyncio.ensure_future(self.packet_callback(ptype, data, error, throttled))

	def _wait_for_response(self, pid):
		future = asyncio.Future()
		self._pending_responses[pid] = future
		return future
