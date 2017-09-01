import logging
logging.basicConfig(level=logging.DEBUG)
import asyncio
asyncio.get_event_loop().set_debug(True)

import json
import websockets
from websockets import ConnectionClosed



class Connection:
	def __init__(self, url, packet_hook, cookie=None):
		self.url = url
		self.cookie = cookie
		self.packet_hook = packet_hook
		
		stopped = False
		
		self._ws = None
		self._pid = 0
		self._pending_responses = {}
	
	async def run(self):
		self._ws = await websockets.connect(self.url)
		
		try:
			while True:
				response = await self._ws.recv()
				asyncio.ensure_future(self._handle_json(response))
		except websockets.ConnectionClosed:
			pass
		finally:
			await self._ws.close() # just to make sure it's closed
			self._ws = None
			stopped = True
			
			for futures in self._pending_responses:
				for future in futures:
					future.set_error(ConnectionClosed)
					future.cancel()
	
	async def stop(self):
		if not stopped and self._ws:
			await self._ws.close()
	
	async def send(ptype, data=None, await_response=True):
		if stopped:
			raise ConnectionClosed
		
		pid = self._new_pid()
		packet["type"] = ptype
		packet["data"] = data
		packet["id"] = pid
		
		if await_response:
			wait_for = self._wait_for_response(pid)
			await self._ws.send(json.dumps(packet))
			await wait_for
			return wait_for.result()
		else:
			await self._ws.send(json.dumps(packet))
	
	def _new_pid(self):
		self._pid += 1
		return self._pid
	
	async def _handle_json(text):
		packet = json.loads(text)
		
		# Deal with pending responses
		pid = packet.get("id")
		for future in self._pending_responses.pop(pid, []):
			future.set_result(packet)
		
		# Pass packet onto room
		await self.packet_hook(packet)
	
	def _wait_for_response(pid):
		future = asyncio.Future()
		
		if pid not in self._pending_responses:
			self._pending_responses[pid] = []
		self._pending_responses[pid].append(future)
		
		return future

def do_nothing(*args, **kwargs):
	pass

def run():
	conn = Connection("wss://echo.websocket.org", do_nothing)
	loop = asyncio.get_event_loop()
	#loop.call_later(3, conn.stop)
	
	loop.run_until_complete(asyncio.ensure_future(conn.run()))
