from datetime import datetime
from typing import List

from config.constants import RedisKeys
from config.settings import BrokerConfig, AppConfig
from controller.context_manager import context_log_meta
from data_adapter.redis import Cache
from logger import logger
from models.sensi_models import SensiBrokerResModel, BrokerWSDataTypes
from utils.utils import make_request

import json

from data_adapter.ws import WS
from models.sensi_models import BrokerWSOutgoingMessage, BrokerWSIncomingMessage


class BrokerIntegration:
    """external broker integration class"""

    @staticmethod
    def fetch_all_underlyings() -> List[SensiBrokerResModel]:
        """fetch all underlyings from broker"""
        response_data, status_code = make_request(BrokerConfig.url + BrokerConfig.underlying_url)
        if status_code != 200 or not response_data.get("success"):
            logger.error(extra=context_log_meta.get(),
                         msg=f"fetch_all_underlyings: Error in fetching underlyings from broker"
                             f" status_code: {status_code} response_data: {response_data}")
            return []
        return [SensiBrokerResModel(**underlying) for underlying in response_data.get("payload")]

    @staticmethod
    def fetch_all_derivatives_by_underlying_token(underlying_token: str) -> List[SensiBrokerResModel]:
        """fetch all derivatives by underlying token from broker"""
        response_data, status_code = make_request(
            BrokerConfig.url + BrokerConfig.derivative_url.format(underlying_token))
        if status_code != 200 or not response_data.get("success"):
            logger.error(extra=context_log_meta.get(),
                         msg=f"fetch_all_derivatives_by_underlying_token: Error in fetching derivatives from broker"
                             f" status_code: {status_code} response_data: {response_data}")
            return []
        return [SensiBrokerResModel(**derivative) for derivative in response_data.get("payload")]

    @staticmethod
    async def broker_ws_listener():
        """connect to websocket and listen for incoming messages
        This should run in a separate thread which should not block the main thread or event loop"""
        await WS.get_instance().connect()
        while True:
            try:
                data = await WS.get_instance().recv()
                message_from_broker = BrokerWSIncomingMessage.parse_raw(data)
                # logger.debug(extra=context_log_meta.get(),
                #              msg=f"broker_ws_listener: message_from_broker: {message_from_broker}")
                if message_from_broker.data_type == BrokerWSDataTypes.ERROR:
                    logger.error(extra=context_log_meta.get(),
                                 msg=f"broker_ws_listener: Error in message from broker: {message_from_broker}"
                                     f"trying to reconnect to websocket")
                    # try to reconnect
                    await WS.get_instance().connect()
                elif message_from_broker.data_type == BrokerWSDataTypes.QUOTE:
                    Cache.get_instance().hset(key=RedisKeys.ENTITY_PRICE_DATA,
                                              mapping={message_from_broker.payload.get("token"):
                                                           message_from_broker.payload.get("price")})
                # register the last ping recieved time in cache
                Cache.get_instance().hset(key=RedisKeys.LAST_PING_TIME_FROM_WS,
                                          mapping={AppConfig.node_id: datetime.now().timestamp()})
            except Exception as e:
                logger.error(extra=context_log_meta.get(),
                             msg=f"broker_ws_listener: exception in broker_ws_listener: {e}")

    @staticmethod
    async def broker_ws_sender(data: json):
        """send data to websocket"""
        await WS.get_instance().send(data)
