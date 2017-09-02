import logging
logging.basicConfig(level=logging.DEBUG)
import asyncio
asyncio.get_event_loop().set_debug(True)

import json
import websockets
#from websockets import ConnectionClosed

__all__ = ["Connection"]



class Connection:
	def __init__(self, url, packet_hook, cookie=None):
		self.url = url
		self.cookie = cookie
		self.packet_hook = packet_hook
		
		self.stopped = False
		
		self._ws = None
		self._pid = 0
		self._pending_responses = {}
	
	async def run(self):
		self._ws = await websockets.connect(self.url, max_size=None)
		
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
			
			for future in self._pending_responses:
				#future.set_error(ConnectionClosed)
				future.cancel()
	
	async def stop(self):
		if not self.stopped and self._ws:
			await self._ws.close()
	
	async def send(self, ptype, data=None, await_response=True):
		if self.stopped:
			raise ConnectionClosed
		
		pid = self._new_pid()
		packet = {
			"type": ptype,
			"data": data,
			"id": str(pid)
		}
		
		if await_response:
			wait_for = self._wait_for_response(pid)
		
		await self._ws.send(json.dumps(packet, separators=(',', ':')))
		
		if await_response:
			await wait_for
			return wait_for.result()
	
	def _new_pid(self):
		self._pid += 1
		return self._pid
	
	async def _handle_json(self, text):
		packet = json.loads(text)
		
		# Deal with pending responses
		pid = packet.get("id")
		future = self._pending_responses.pop(pid, None)
		if future:
			future.set_result(packet)
		
		# Pass packet onto room
		await self.packet_hook(packet)
	
	def _wait_for_response(self, pid):
		future = asyncio.Future()
		self._pending_responses[pid] = future
		
		return future

#async def handle_packet(packet):
	#if packet.get("type") == "ping-event":
		#await c._ws.send('{"type":"ping-reply","data":{"time":' + str(packet.get("data").get("time")) + '}}')
		##await c.send("ping-reply", {"time": packet.get("data").get("time")}, False)

#c = Connection("wss://euphoria.io/room/test/ws", handle_packet)

async def await_future(f):
	await f
	print(f.result())

def run():
	f = asyncio.Future()
	#f.set_result("Hello World!")
	f.cancel()
	#f.set_result("Hello World!")
	
	loop = asyncio.get_event_loop()
	loop.run_until_complete(await_future(f))
	#loop.run_until_complete(c.run())
