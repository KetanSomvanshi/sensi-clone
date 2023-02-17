import http

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import requests
from controller.context_manager import context_log_meta
from logger import logger
from models.base import GenericResponseModel


def build_api_response(generic_response: GenericResponseModel) -> JSONResponse:
    try:

        status_code = http.HTTPStatus.OK if generic_response.success else http.HTTPStatus.UNPROCESSABLE_ENTITY
        response_json = jsonable_encoder(generic_response)
        res = JSONResponse(status_code=status_code, content=response_json)
        logger.info(extra=context_log_meta.get(),
                    msg="build_api_response: Generated Response with status_code: {status_code}")
        return res
    except Exception as e:
        logger.error(extra=context_log_meta.get(), msg=f"exception in build_api_response error : {e}")
        response_json = jsonable_encoder(GenericResponseModel(success=False))
        return JSONResponse(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, content=response_json)


def make_request(external_service_url, request_params: dict = None, method='GET', headers=None) -> (dict, int):
    try:
        request_headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if headers is not None:
            request_headers.update(headers)
        response = requests.request(method=method, url=external_service_url, params=request_params,
                                    headers=request_headers, timeout=10)
        result_response, status_code = response.json(), response.status_code
        logger.debug(extra=context_log_meta.get(),
                     msg=f"make_request: Successfully made request to external service: {external_service_url}"
                         f" with status_code: {status_code} data= {result_response}")
        return result_response, status_code
    except Exception as e:
        logger.error(extra=context_log_meta.get(), msg=f"exception in make_request error : {e}")
        return {}, 500
