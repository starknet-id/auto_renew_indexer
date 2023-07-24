

from listener import Listener
from aiohttp import web

async def is_ready(request):
    endpoint = request.app['endpoint']
    block_number = endpoint.on_endpoint()
    return web.json_response(block_number)

class Endpoints:
  def __init__(self, listener : Listener):
    self.listener = listener

  def on_endpoint(self):
    return { "last_block": self.listener.last_block_number}