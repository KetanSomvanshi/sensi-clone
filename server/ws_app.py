import asyncio
import json

import websockets

from config.constants import RedisKeys
from config.settings import BrokerConfig
from data_adapter.redis import Cache
from data_adapter.ws import WS


async def listener():
    await WS.get_instance().connect()
    while True:
        data = await WS.get_instance().recv()
        print(data)
        # await WS.get_instance().send("queue")
        # print(data)

        # async with websockets.connect(BrokerConfig.ws_url) as websocket:
        #     # await websocket.send("queue")
        #     print(await websocket.recv())


async def sender(data: json):
    pass
    # async with WS.get_instance() as websocket:
    #     websocket.send(json)
#
# async def close():
#
#     await websocket.close()
