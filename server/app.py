#!/usr/bin/env python3
import asyncio
import threading

import uvicorn
from fastapi import FastAPI

from config.constants import RedisKeys
from config.settings import AppConfig
from controller import status, sensi_controller
from data_adapter import db
from data_adapter.redis import Cache
from integrations.broker_integration import BrokerIntegration
from logger import logger
from usecases.sensi_usecase import SensiUseCase

app = FastAPI()

db.DBBase.metadata.create_all(bind=db.db_engine)

app.include_router(status.router)
app.include_router(sensi_controller.sensi_router)

"""we are trying to bound the asynchronous functions to a thread so that we can run them in a synchronous manner
inside the background threads
We would create a new event loop for each thread and run the asynchronous functions in that event loop
"""


async def redis_subscriber_callback():
    await SensiUseCase.subscribe_and_poll_topic_data()


def redis_subscriber_between_callback():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(redis_subscriber_callback())
    loop.close()


# async def broker_ws_listener_callback():
#     await BrokerIntegration.broker_ws_listener()
#
#
# def broker_ws_callback_listener():
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(broker_ws_listener_callback())
#     loop.close()


@app.on_event("startup")
async def startup_event():
    """this is the startup event which will be called when the fastapi server starts"""
    logger.info("Startup Event Triggered node_id: {}".format(AppConfig.node_id))
    try:
        """start a background thread to subscribe to redis and poll for broker ws listener"""
        logger.info("Starting background thread for redis subscriber")
        _redis_subscriber_thread = threading.Thread(target=redis_subscriber_between_callback, args=())
        _redis_subscriber_thread.start()
        logger.info("Starting background thread for broker ws listener")
        # _broker_ws_listener_thread = threading.Thread(target=broker_ws_callback_listener, args=())
        # _broker_ws_listener_thread.start()

        #  for WS we can use existing app server event loop instead of creating new event loop in a new thread
        asyncio.create_task(BrokerIntegration.broker_ws_listener())
        # register the node id in redis nodes list
        Cache.get_instance().hset(key=RedisKeys.NODE_IDS_IN_CLUSTER, mapping={AppConfig.node_id: 1})
        logger.info("Startup Event Completed node_id = {}".format(AppConfig.node_id))
    except Exception as e:
        logger.error(f"Error while connecting to websocket {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutdown Event Triggered")
    # TODO : handle closing down of threads and ws connection and redis connection


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=19093, reload=True)
