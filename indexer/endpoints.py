

from listener import Listener
from aiohttp import web

async def is_ready(request):
    endpoint = request.app['endpoint']
    block_number = endpoint.on_endpoint()
    return web.json_response(block_number)

async def get_renewal_data(request):
    address = request.query.get('address')
    domain = request.query.get('domain')

    collection = request.app['collection']
    documents = collection.find({"renewer_address": str(address), "domain": str(domain), "_chain.valid_to": None})
    documents_list = [doc for doc in documents]
    for document in documents_list:
        document.pop('_id', None)
        document.pop('_chain', None)

    if documents_list:
        return web.json_response(documents_list[0])
    else:
      return web.json_response({"error": "no entries found"})

class Endpoints:
  def __init__(self, listener : Listener):
    self.listener = listener

  def on_endpoint(self):
    return { "last_block": self.listener.last_block_number}