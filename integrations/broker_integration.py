from typing import List

from config.settings import BrokerConfig
from controller.context_manager import context_log_meta
from logger import logger
from models.sensi_models import SensiBrokerResModel
from utils.utils import make_request


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
