import http

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

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
