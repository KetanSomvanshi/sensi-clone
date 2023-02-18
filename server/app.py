#!/usr/bin/env python3
import asyncio

from fastapi import FastAPI, Depends

from config.constants import RedisKeys
from controller import status, sensi_controller
from data_adapter import db
from data_adapter.redis import Cache
from data_adapter.ws import WS
from logger import logger
import uvicorn

from server.ws_app import listener
from usecases.sensi_usecase import SensiUseCase

app = FastAPI()

db.DBBase.metadata.create_all(bind=db.db_engine)

app.include_router(status.router)
app.include_router(sensi_controller.sensi_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Startup Event Triggered")
    try:
        # asyncio.get_event_loop().run_until_complete(SensiUseCase.subscribe_and_poll_to_derivative_data())
        asyncio.create_task(listener())
    except Exception as e:
        logger.error(f"Error while connecting to websocket {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutdown Event Triggered")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=19093, reload=True)
