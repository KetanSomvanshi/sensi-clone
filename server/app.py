#!/usr/bin/env python3
import asyncio
import threading

import uvicorn
from fastapi import FastAPI

from controller import status, sensi_controller
from data_adapter import db
from logger import logger
from server.ws_app import listener
from usecases.sensi_usecase import SensiUseCase

app = FastAPI()

db.DBBase.metadata.create_all(bind=db.db_engine)

app.include_router(status.router)
app.include_router(sensi_controller.sensi_router)


async def some_callback():
    await SensiUseCase.subscribe_and_poll_to_derivative_data()


def between_callback():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(some_callback())
    loop.close()


@app.on_event("startup")
async def startup_event():
    logger.info("Startup Event Triggered")
    try:
        asyncio.create_task(listener())
        _thread = threading.Thread(target=between_callback, args=())
        _thread.start()
    except Exception as e:
        logger.error(f"Error while connecting to websocket {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutdown Event Triggered")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=19093, reload=True)
