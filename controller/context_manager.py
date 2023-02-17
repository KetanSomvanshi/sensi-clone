from contextvars import ContextVar

import uuid
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from data_adapter.db import get_db
from logger import logger

# we are using context variables to store request level context , as FASTAPI
# does not provide request context out of the box
context_db_session: ContextVar[Session] = ContextVar('db_session', default=None)
context_api_id: ContextVar[str] = ContextVar('api_id')
context_log_meta: ContextVar[dict] = ContextVar('log_meta', default={})


async def build_request_context(request: Request,
                                db: Session = Depends(get_db)):
    # set the db-session in context-var so that we don't have to pass this dependency downstream
    context_db_session.set(db)
    context_api_id.set(str(uuid.uuid4()))
    context_log_meta.set({'api_id': context_api_id.get(), 'request_id': request.headers.get('X-Request-ID')})
    logger.info(extra={"api_id": context_api_id.get()}, msg="REQUEST_INITIATED")


def get_db_session() -> Session:
    db = context_db_session.get()
    return db
