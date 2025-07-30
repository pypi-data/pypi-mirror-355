import json,logging
from typing import Any
from localstack.http.websocket import WebSocket,WebSocketDisconnectedError,WebSocketRequest
from eventstudio.utils.utils import CustomJSONEncoder
LOG=logging.getLogger(__name__)
class EventStreamerService:
	sockets:list[WebSocket]
	def __init__(A):A.sockets=[]
	def on_websocket_request(B,request:WebSocketRequest,*D,**E):
		A=None
		try:
			with request.accept()as A:
				B.sockets.append(A)
				while True:C=A.receive();LOG.info('Received message from log streamer websocket: %s',C)
		except WebSocketDisconnectedError:LOG.debug('Websocket disconnected: %s',A)
		finally:
			if A is not None and A in B.sockets:B.sockets.remove(A)
	def notify(B,doc:Any):
		C=json.dumps(doc,cls=CustomJSONEncoder)
		for A in list(B.sockets):
			try:A.send(C)
			except Exception as D:
				LOG.warning('Failed to send to socket %s: %s. Removing socket.',A,D)
				if A in B.sockets:B.sockets.remove(A)
	def close(A):
		for B in list(A.sockets):
			try:B.close()
			except Exception as C:LOG.error('Error closing websocket: %s',C)
		A.sockets.clear()