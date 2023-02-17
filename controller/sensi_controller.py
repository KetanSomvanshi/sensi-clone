import http

from fastapi import APIRouter, Depends, Path

from controller.context_manager import build_request_context
from models.base import GenericResponseModel
from usecases.sensi_usecase import SensiUseCase
from utils.utils import build_api_response

sensi_router = APIRouter(prefix="", tags=["sensi", "sensi_underlying", "sensi_derivative"])


#  api to list all underlying
@sensi_router.get("/underlying-prices", status_code=http.HTTPStatus.OK)
async def get_underlying_prices(_=Depends(build_request_context)):
    """
    Get underlying prices
    :param _: build_request_context dependency injection handles the request context
    :return:
    """
    response: GenericResponseModel = SensiUseCase.get_underlying_prices()
    return build_api_response(response)


# api to list all derivative prices for underlying symbol
@sensi_router.get("/derivative-prices/{symbol}", status_code=http.HTTPStatus.OK)
async def get_derivative_prices(_=Depends(build_request_context), symbol: str = Path(...)):
    """
    Get derivative prices for underlying symbol
    :param _: build_request_context dependency injection handles the request context
    :param symbol: underlying symbol
    :return:
    """
    response: GenericResponseModel = SensiUseCase.get_derivatives_by_underlying_symbol(symbol=symbol)
    return build_api_response(response)
