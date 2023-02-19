import time
from datetime import datetime, timedelta
from typing import List, Set

from config.constants import RedisKeys
from config.settings import AppConfig, BrokerConfig
from controller.context_manager import context_log_meta
from data_adapter.redis import Cache
from data_adapter.sensi_data import SensiUnderlying, SensiDerivative
from data_adapter.ws import WS
from integrations.broker_integration import BrokerIntegration
from logger import logger
from models.base import GenericResponseModel
from models.sensi_models import SensiUnderlyingModel, SensiDerivativeModel, SensiBrokerResModel, UnderlyingCacheModel, \
    BrokerWSOutgoingMessage, BrokerWSCommands, SensiResModel


class SensiUseCase:

    @staticmethod
    def get_underlying_prices() -> GenericResponseModel:
        """
        Get underlying prices
        :return GenericResponseModel:
        """
        try:
            sensi_underlyings: List[SensiResModel] = SensiUnderlying.get_all_underlying()
            if not sensi_underlyings:
                return GenericResponseModel(success=False, payload="No underlyings found")
            token_price_from_cache: dict = Cache.get_instance(). \
                hmget(RedisKeys.ENTITY_PRICE_DATA, fields=[underlying.token for underlying in sensi_underlyings])
            # build a map of token and price from list of derivatives
            token_price_map: dict = {}
            for i in range(len(sensi_underlyings)):
                if token_price_from_cache[i]:
                    token_price_map[sensi_underlyings[i].token] = float(token_price_from_cache[i])
            # update price in derivative object from cache
            for derivative in sensi_underlyings:
                derivative.price = token_price_map.get(derivative.token)
            return GenericResponseModel(success=True, payload=sensi_underlyings)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"exception in get_underlying_prices error : {e}")
            return GenericResponseModel(success=False)

    @staticmethod
    def get_derivatives_by_underlying_symbol(symbol: str) -> GenericResponseModel:
        """
        Get derivative prices for underlying symbol
        :param symbol: underlying symbol
        :return GenericResponseModel:
        """
        try:
            sensi_derivatives: List[SensiResModel] = SensiDerivative.get_all_derivative_by_underlying_symbol(
                symbol=symbol)
            if not sensi_derivatives:
                return GenericResponseModel(success=False, payload="No derivatives found for given symbol")
            token_price_from_cache: dict = Cache.get_instance(). \
                hmget(RedisKeys.ENTITY_PRICE_DATA, fields=[derivative.token for derivative in sensi_derivatives])
            # build a map of token and price from list of derivatives
            token_price_map: dict = {}
            for i in range(len(sensi_derivatives)):
                if token_price_from_cache[i]:
                    token_price_map[sensi_derivatives[i].token] = float(token_price_from_cache[i])
            # update price in derivative object from cache
            for derivative in sensi_derivatives:
                derivative.price = token_price_map.get(derivative.token)
            return GenericResponseModel(success=True, payload=sensi_derivatives)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"exception in get_derivatives_by_symbol error : {e}")
            return GenericResponseModel(success=False)

    @staticmethod
    def sync_underlyings_data() -> GenericResponseModel:
        """
        Sync underlying data
        :return GenericResponseModel:
        """
        try:
            underlyings_from_broker: List[SensiBrokerResModel] = BrokerIntegration.fetch_all_underlyings()
            current_underlyings_in_system: Set[str] = SensiUseCase.get_all_underlyings_from_cache()
            #  filter out underlyings which are already in system
            underlyings_to_be_added: List[SensiBrokerResModel] = list(
                filter(lambda x: x.token not in current_underlyings_in_system, underlyings_from_broker))
            if not underlyings_to_be_added:
                logger.error(extra=context_log_meta.get(), msg=f"no underlyings found in broker that are not in system")
                return GenericResponseModel(success=False)
            underlyings_to_insert = [underlying.build_underlying_db_model() for underlying in underlyings_to_be_added]
            SensiUnderlying.insert_underlyings(underlyings_to_insert)
            # update cached underlyings with newly added underlyings
            SensiUseCase.add_underlyings_in_cache([UnderlyingCacheModel(token=underlying.token, id=underlying.id) for
                                                   underlying in underlyings_to_insert])
            SensiUseCase.publish_synced_entity_data([underlying.token for underlying in underlyings_to_insert])
            return GenericResponseModel(success=True)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"exception in sync_underlyings_data error : {e}")
            return GenericResponseModel(success=False)

    @staticmethod
    def sync_derivatives_data() -> GenericResponseModel:
        """
        Sync derivative data for all underlyings
        :return GenericResponseModel:
        """
        try:
            udnerlyings_from_system: List[UnderlyingCacheModel] = SensiUseCase.get_underlyings_token_id_from_cache()
            if not udnerlyings_from_system:
                logger.error(extra=context_log_meta.get(), msg=f"no underlyings found in db")
                return GenericResponseModel(success=False)
            derivative_tokens_to_subscribe_from_ws: List[str] = []
            for underlying in udnerlyings_from_system:
                derivatives_from_broker: List[
                    SensiBrokerResModel] = BrokerIntegration.fetch_all_derivatives_by_underlying_token(
                    underlying_token=underlying.token)
                current_derivatives_in_system: Set[str] = SensiUseCase.get_all_derivatives_from_cache(
                    underlying_token=underlying.token)
                #  filter out derivatives which are already in system
                derivatives_to_be_added: List[SensiBrokerResModel] = list(
                    filter(lambda x: x.token not in current_derivatives_in_system, derivatives_from_broker))
                if not derivatives_to_be_added:
                    logger.error(extra=context_log_meta.get(),
                                 msg=f"no derivatives found in broker that are not in system "
                                     f"for underlying : {underlying.token}")
                    continue
                SensiDerivative.insert_derivatives(
                    [derivative.build_derivative_db_model(underlying_id=underlying.id) for derivative in
                     derivatives_to_be_added])
                # update cached derivatives with newly added derivatives
                token_to_add_in_cache = [derivative.token for derivative in derivatives_to_be_added]
                SensiUseCase.add_derivatives_in_cache(
                    underlying_token=underlying.token,
                    derivatives=token_to_add_in_cache)
                derivative_tokens_to_subscribe_from_ws.extend(token_to_add_in_cache)
            # add newly added derivatives to set of tokens to subscribe from ws
            if derivative_tokens_to_subscribe_from_ws:
                SensiUseCase.publish_synced_entity_data(derivative_tokens_to_subscribe_from_ws)
            return GenericResponseModel(success=True)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"exception in sync_derivatives_data error : {e}")
            return GenericResponseModel(success=False)

    @staticmethod
    def get_all_underlyings_from_cache() -> Set[str]:
        """extract only underlying tokens and return"""
        underlyings = {UnderlyingCacheModel.parse_cache_data(data).token for data in
                       Cache.get_instance().smembers(RedisKeys.UNDERLYINGS_DATA)}
        if not underlyings:
            # if cache is empty then fetch from db
            logger.error(extra=context_log_meta.get(), msg=f"no underlyings found in cache fetching form db")
            underlying_from_db = SensiUnderlying.get_all_underlyings()
            if not underlying_from_db:
                logger.error(extra=context_log_meta.get(), msg=f"no underlyings found in db")
                return set()
            SensiUseCase.add_underlyings_in_cache([UnderlyingCacheModel(token=underlying.token, id=underlying.id) for
                                                   underlying in underlying_from_db])
            underlyings = {underlying.token for underlying in underlying_from_db}
        return underlyings

    @staticmethod
    def get_underlyings_token_id_from_cache() -> List[UnderlyingCacheModel]:
        """extract underlying tokens and ids and return"""
        underlyings = [UnderlyingCacheModel.parse_cache_data(data) for data in
                       Cache.get_instance().smembers(RedisKeys.UNDERLYINGS_DATA)]
        if not underlyings:
            # if cache is empty then fetch from db
            logger.error(extra=context_log_meta.get(), msg=f"no underlyings found in cache fetching form db")
            underlying_from_db = SensiUnderlying.get_all_underlyings()
            if not underlying_from_db:
                logger.error(extra=context_log_meta.get(),
                             msg=f"no underlyings found in db...syncing underlying from broker")
                SensiUseCase.sync_underlyings_data()
                underlyings = [UnderlyingCacheModel.parse_cache_data(data) for data in
                               Cache.get_instance().smembers(RedisKeys.UNDERLYINGS_DATA)]
                if not underlyings:
                    logger.error(extra=context_log_meta.get(), msg=f"no underlyings found in broker")
                    return []
                return underlyings
            SensiUseCase.add_underlyings_in_cache([UnderlyingCacheModel(token=underlying.token, id=underlying.id) for
                                                   underlying in underlying_from_db])
            underlyings = [UnderlyingCacheModel(token=underlying.token, id=underlying.id) for underlying in
                           underlying_from_db]
        return underlyings

    @staticmethod
    def add_underlyings_in_cache(underlyings: List[UnderlyingCacheModel]) -> int:
        """we need to store id and token both in cache because we need id to build derivative db models"""
        return Cache.get_instance().sadd(RedisKeys.UNDERLYINGS_DATA,
                                         values=[underlying.build_cache_data() for underlying in underlyings])

    @staticmethod
    def get_all_derivatives_from_cache(underlying_token: str) -> Set[str]:
        """extract derivatives associated with underlying token"""
        derivatives = Cache.get_instance().smembers(RedisKeys.DERIVATIVES_DATA.format(underlying_token))
        if not derivatives:
            # if cache is empty then fetch from db
            logger.error(extra=context_log_meta.get(), msg=f"no derivatives found in cache fetching form db")
            derivatives_from_db = SensiDerivative.get_all_derivatives_by_underlying_token(underlying_token)
            if not derivatives_from_db:
                logger.error(extra=context_log_meta.get(), msg=f"no derivatives found in db")
                return set()
            SensiUseCase.add_derivatives_in_cache(underlying_token=underlying_token,
                                                  derivatives=[derivative.token for derivative in
                                                               derivatives_from_db])
            derivatives = {derivative.token for derivative in derivatives_from_db}
        return derivatives

    @staticmethod
    def add_derivatives_in_cache(underlying_token: str, derivatives: List[str]) -> int:
        """add derivatives in cache"""
        return Cache.get_instance().sadd(RedisKeys.DERIVATIVES_DATA.format(underlying_token), values=derivatives)

    """we are using combination of set and redis pubsub to send data from worker to application servers
    worker would publish an event on topic and add data in set , app instance would subscribe to topic and
    read data from set and process it , at a time only one instance would be able to read data from set and other 
    instances would get empty data"""

    @staticmethod
    def publish_synced_entity_data(synced_entity_tokens: List[str]):
        """publish synced derivatives data to redis"""
        Cache.get_instance().sadd_and_publish(topic=RedisKeys.TOPIC_FOR_WS_ENTITY_PUSH,
                                              msg=RedisKeys.TOPIC_MESSAGE_FOR_WS_ENTITY_PUSH,
                                              key=RedisKeys.ENTITY_TOKENS_TO_BE_SYNCED, values=synced_entity_tokens)

    @staticmethod
    async def subscribe_and_poll_topic_data():
        """subscribe to derivative data and poll for data
        in cae of multiple instances of servers , all instances would subscribe to the topic and receive message
        but only one of them would get hold of data present in set
        """
        Cache.get_instance().subscribe(RedisKeys.TOPIC_FOR_WS_ENTITY_PUSH)
        Cache.get_instance().subscribe(RedisKeys.TOPIC_FOR_WS_RECONNECT)
        while True:
            try:
                message = Cache.get_instance().get_message()
                if message and message.get("data") == RedisKeys.TOPIC_MESSAGE_FOR_WS_ENTITY_PUSH:
                    derivatives_to_subscribe: List[str] = Cache.get_instance().smembers_and_delete(
                        key=RedisKeys.ENTITY_TOKENS_TO_BE_SYNCED)
                    # in cae of multiple instances of servers , all instances would subscribe to the topic but only on
                    # of them would get hold of data present in the redis set
                    if not derivatives_to_subscribe:
                        continue
                    #  subscribe to derivatives data from WS
                    logger.info(extra=context_log_meta.get(),
                                msg=f"subscribe_and_poll_topic_data: subscribing to derivatives data from ws "
                                    f": {derivatives_to_subscribe}")
                    await BrokerIntegration.broker_ws_sender(
                        data=BrokerWSOutgoingMessage(msg_command=BrokerWSCommands.SUBSCRIBE,
                                                     tokens=derivatives_to_subscribe).json())
                    # register the entity token as ws subscriber for the node
                    # if this node goes down , orchestrator would register these entity ws subscribers to other node
                    Cache.get_instance().sadd(key=RedisKeys.NODE_ID_WS_ENTITY_MAPPING.format(AppConfig.node_id),
                                              values=derivatives_to_subscribe)
                    logger.info(extra=context_log_meta.get(),
                                msg=f"subscribe_and_poll_topic_data: subscribed to derivatives data from ws "
                                    f": {derivatives_to_subscribe}")
                elif message and message.get("channel") == RedisKeys.TOPIC_FOR_WS_RECONNECT and message.get(
                        "data") == AppConfig.node_id:
                    # if node instance get a message on topic to reconnect  and node id in message matched its own node
                    # id then it would reconnect to ws
                    logger.info(extra=context_log_meta.get(),
                                msg=f"subscribe_and_poll_topic_data: reconnecting to ws")
                    await WS.get_instance().connect()
                    logger.info(extra=context_log_meta.get(),
                                msg=f"subscribe_and_poll_topic_data: reconnected to ws")
            except Exception as e:
                logger.error(extra=context_log_meta.get(),
                             msg=f"exception in subscribe_and_poll_to_derivative_data : {e}")
            finally:
                # poll every second
                time.sleep(1)

    """WS reconnect logic , we would register last ping against node id in redis hashset 
    worker would keep on checking if last ping is older than 60 seconds , if yes then it would
    publish a node_id as message on topic TOPIC_FOR_WS_RECONNECT
     reciever node would check if it's node id matches with message and if yes then it would
        reconnect to ws"""

    @staticmethod
    def check_ws_connection_alive():
        """check if ws connection is alive """
        node_id_last_ping_map: dict = Cache.get_instance().hgetall(RedisKeys.LAST_PING_TIME_FROM_WS)
        current_time = datetime.now()
        for node_id, last_ping in node_id_last_ping_map.items():
            if current_time - datetime.fromtimestamp(float(last_ping)) > timedelta(
                    seconds=BrokerConfig.ws_ping_timeout):
                logger.error(extra=context_log_meta.get(),
                             msg=f"check_ws_connection_alive: ws connection is not alive for node_id : {node_id}")
                Cache.get_instance().publish(RedisKeys.TOPIC_FOR_WS_RECONNECT, node_id)
                logger.info(extra=context_log_meta.get(),
                            msg=f"check_ws_connection_alive: published message node id : {node_id} on topic "
                                f"{RedisKeys.TOPIC_FOR_WS_RECONNECT}")
