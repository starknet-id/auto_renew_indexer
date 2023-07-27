import asyncio
import traceback
from endpoints import Endpoints
from endpoints import is_ready, get_renewal_data
from listener import Listener
from apibara.indexer import IndexerRunner, IndexerRunnerConfiguration
from config import TomlConfig
from aiohttp import web
from pymongo import MongoClient
import aiohttp_cors

async def start_server(conf, events_manager):
    app = web.Application()
    app.add_routes([web.get('/is_ready', is_ready)])
    app.add_routes([web.get('/get_renewal_data', get_renewal_data)])
    app['endpoint'] = Endpoints(events_manager)
    client = MongoClient(conf.connection_string)
    db = client[conf.indexer_id]
    app['collection'] = db['auto_renewals']
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )
    for route in list(app.router.routes()):
        cors.add(route)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=conf.server_port)
    await site.start()
    stop_event = asyncio.Event()
    await stop_event.wait()
    return runner

async def main():
    conf = TomlConfig("config.toml", "config.template.toml")
    events_manager = Listener(conf)
    enable_ssl = False if conf.is_devnet is True else True
    runner = IndexerRunner(
        config=IndexerRunnerConfiguration(
            stream_url=conf.apibara_stream,
            storage_url=conf.connection_string,
            token=conf.token,
            stream_ssl=enable_ssl,
        ),
        reset_state=conf.reset_state,
    )

    runner_task = asyncio.create_task(runner.run(events_manager, ctx={"network": "starknet-mainnet"}))
    server_runner = await start_server(conf, events_manager)
    web_server_task = asyncio.create_task(server_runner.start())

    await asyncio.gather(runner_task, web_server_task)
    print("starknetid indexer started")
    print('web_server started')
    return server_runner


if __name__ == "__main__":
    while True:
        try:
            server_runner = asyncio.run(main())
        except Exception:
            print(traceback.format_exc())
            print("warning: exception detected, restarting")
            if server_runner is not None:
                asyncio.run(server_runner.cleanup())
