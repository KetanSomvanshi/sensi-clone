from controller.context_manager import context_log_meta, build_non_request_context
from logger import logger
from models.base import GenericResponseModel
from worker.celery import celery_app, SQLAlchemyTask
from usecases.sensi_usecase import SensiUseCase

"""command to run worker - 'celery -A worker.task_worker worker -B'"""


@celery_app.task(base=SQLAlchemyTask)
def trigger_underlyings_sync() -> GenericResponseModel:
    """ This is a celery task which is triggered by scheduler to sync underlyings
    Internally this would call the usecase as usecase has business logic to sync underlyings """
    logger.info(extra=context_log_meta.get(), msg="trigger_underlyings_sync: Triggered")
    build_non_request_context()
    response: GenericResponseModel = SensiUseCase().sync_underlyings_data()
    if not response.success:
        logger.error(extra=context_log_meta.get(),
                     msg=f"trigger_underlyings_sync: Error in syncing underlyings data from broker")
    logger.info(extra=context_log_meta.get(),
                msg="trigger_underlyings_sync: Syncing underlyings data from broker completed")
    return response


@celery_app.task(base=SQLAlchemyTask)
def trigger_derivatives_sync() -> GenericResponseModel:
    """ This is a celery task which is triggered by scheduler to sync derivatives
    Internally this would call the usecase as usecase has business logic to sync derivatives """
    logger.info(extra=context_log_meta.get(), msg="trigger_derivatives_sync: Triggered")
    build_non_request_context()
    response: GenericResponseModel = SensiUseCase().sync_derivatives_data()
    if not response.success:
        logger.error(extra=context_log_meta.get(),
                     msg=f"trigger_derivatives_sync: Error in syncing derivatives data from broker")
    logger.info(extra=context_log_meta.get(),
                msg="trigger_derivatives_sync: Syncing derivatives data from broker completed")
    return response


@celery_app.task
def check_ws_connection_alive():
    """ This is a celery task which is triggered by scheduler to check if websocket connection is alive
    If not alive, it would try to reconnect """
    logger.info(extra=context_log_meta.get(), msg="check_ws_connection_alive: Triggered")
    build_non_request_context()
    response: GenericResponseModel = SensiUseCase().check_ws_connection_alive()
    if not response.success:
        logger.error(extra=context_log_meta.get(),
                     msg=f"check_ws_connection_alive: Error in checking websocket connection alive")
    logger.info(extra=context_log_meta.get(),
                msg="check_ws_connection_alive: Checking websocket connection alive completed")
    return response
