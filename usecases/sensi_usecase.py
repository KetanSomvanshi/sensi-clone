from typing import List

from controller.context_manager import context_log_meta
from data_adapter.sensi_data import SensiUnderlying, SensiDerivative
from integrations.broker_integration import BrokerIntegration
from logger import logger
from models.base import GenericResponseModel
from models.sensi_models import SensiUnderlyingModel, SensiDerivativeModel, SensiBrokerResModel


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
            if not underlyings_from_broker:
                logger.error(extra=context_log_meta.get(), msg=f"no underlyings found in broker")
                return GenericResponseModel(success=False)
            SensiUnderlying.insert_underlyings(
                [underlying.build_underlying_db_model() for underlying in underlyings_from_broker])
            # for underlying in underlyings_from_broker:
            #     BrokerIntegration.fetch_all_derivatives_by_underlying_token(underlying_token=underlying.token)

            return GenericResponseModel(success=True)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"exception in sync_underlyings_data error : {e}")
            return GenericResponseModel(success=False)
