import websockets

from config.settings import BrokerConfig
from utils.utils import Singleton


@Singleton
class WS:
    """abstract layer for websockets , using singleton pattern here to avoid multiple connections
    for the same application instance
    We would be creating single websocket connection for the application instance and utilizing it for all the
    websocket related operations"""

    def __init__(self):
        self.__url = BrokerConfig.ws_url
        self.__ws = None

    async def connect(self):
        """ideally connect should be called only once"""
        self.__ws = await websockets.connect(self.__url)

    async def send(self, msg):
        await self.__ws.send(msg)

    async def recv(self):
        return await self.__ws.recv()

    async def close(self):
        await self.__ws.close()
