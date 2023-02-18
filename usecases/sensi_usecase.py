import time
from typing import List, Set

from config.constants import RedisKeys
from controller.context_manager import context_log_meta
from data_adapter.redis import Cache
from data_adapter.sensi_data import SensiUnderlying, SensiDerivative
from integrations.broker_integration import BrokerIntegration
from logger import logger
from models.base import GenericResponseModel
from models.sensi_models import SensiUnderlyingModel, SensiDerivativeModel, SensiBrokerResModel, UnderlyingCacheModel, \
    BrokerWSOutgoingMessage, BrokerWSCommands


class SensiUseCase:

    @staticmethod
    def get_underlying_prices() -> GenericResponseModel:
        """
        Get underlying prices
        :return GenericResponseModel:
        """
        try:
            sensi_underlyings: List[SensiUnderlyingModel] = SensiUnderlying.get_all_underlying()
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
            sensi_derivatives: List[SensiDerivativeModel] = SensiDerivative.get_all_derivative_by_underlying_symbol(
                symbol=symbol)
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
                SensiUseCase.publish_synced_derivatives_data(derivative_tokens_to_subscribe_from_ws)
            return GenericResponseModel(success=True)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"exception in sync_derivatives_data error : {e}")
            return GenericResponseModel(success=False)

    @staticmethod
    def get_all_underlyings_from_cache() -> Set[str]:
        """extract only underlying tokens and return"""
        return {UnderlyingCacheModel.parse_cache_data(data).token for data in
                Cache.get_instance().smembers(RedisKeys.UNDERLYINGS_DATA)}

    @staticmethod
    def get_underlyings_token_id_from_cache() -> List[UnderlyingCacheModel]:
        """extract underlying tokens and ids and return"""
        return [UnderlyingCacheModel.parse_cache_data(data) for data in
                Cache.get_instance().smembers(RedisKeys.UNDERLYINGS_DATA)]

    @staticmethod
    def add_underlyings_in_cache(underlyings: List[UnderlyingCacheModel]) -> int:
        """we need to store id and token both in cache because we need id to build derivative db models"""
        return Cache.get_instance().sadd(RedisKeys.UNDERLYINGS_DATA,
                                         values=[underlying.build_cache_data() for underlying in underlyings])

    @staticmethod
    def get_all_derivatives_from_cache(underlying_token: str) -> Set[str]:
        """extract derivatives associated with underlying token"""
        return Cache.get_instance().smembers(RedisKeys.DERIVATIVES_DATA.format(underlying_token))

    @staticmethod
    def add_derivatives_in_cache(underlying_token: str, derivatives: List[str]) -> int:
        """add derivatives in cache"""
        return Cache.get_instance().sadd(RedisKeys.DERIVATIVES_DATA.format(underlying_token), values=derivatives)

    """we are using combination of set and redis pubsub to send data from worker to application servers
    worker would publish an event on topic and add data in set , app instance would subscribe to topic and
    read data from set and process it , at a time only one instance would be able to read data from set and other 
    instances would get empty data"""

    @staticmethod
    def publish_synced_derivatives_data(synced_derivatives: List[str]):
        """publish synced derivatives data to redis"""
        Cache.get_instance().sadd_and_publish(topic=RedisKeys.TOPIC_FOR_WS_DERIVAIVE_PUSH,
                                              msg=RedisKeys.TOPIC_MESSAGE_FOR_WS_DERIVAIVE_PUSH,
                                              key=RedisKeys.WS_FOR_DERIVATIVES_DATA, values=synced_derivatives)

    @staticmethod
    async def subscribe_and_poll_to_derivative_data():
        """subscribe to derivative data and poll for data
        in cae of multiple instances of servers , all instances would subscribe to the topic and receive message
        but only one of them would get hold of data present in set
        """
        Cache.get_instance().subscribe(RedisKeys.TOPIC_FOR_WS_DERIVAIVE_PUSH)
        while True:
            try:
                message = Cache.get_instance().get_message()
                if message and message.get("data") == RedisKeys.TOPIC_MESSAGE_FOR_WS_DERIVAIVE_PUSH:
                    derivatives_to_subscribe: List[str] = Cache.get_instance().smembers_and_delete(
                        key=RedisKeys.WS_FOR_DERIVATIVES_DATA)
                    # in cae of multiple instances of servers , all instances would subscribe to the topic but only on
                    # of them would get hold of data present in the redis set
                    if not derivatives_to_subscribe:
                        continue
                    #  subscribe to derivatives data from WS
                    logger.info(extra=context_log_meta.get(),
                                msg=f"subscribe_and_poll_to_derivative_data: subscribing to derivatives data from ws "
                                    f": {derivatives_to_subscribe}")
                    await BrokerIntegration.broker_ws_sender(
                        data=BrokerWSOutgoingMessage(msg_command=BrokerWSCommands.SUBSCRIBE,
                                                     tokens=derivatives_to_subscribe).json())
                    logger.info(extra=context_log_meta.get(),
                                msg=f"subscribe_and_poll_to_derivative_data: subscribed to derivatives data from ws "
                                    f": {derivatives_to_subscribe}")
            except Exception as e:
                logger.error(extra=context_log_meta.get(),
                             msg=f"exception in subscribe_and_poll_to_derivative_data : {e}")
            finally:
                time.sleep(10)
