from datetime import datetime
from urllib.parse import quote_plus

from pytz import timezone
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.orm import sessionmaker

from config.settings import DB
from logger import logging

DBTYPE_POSTGRES = 'postgresql'
CORE_SQLALCHEMY_DATABASE_URI = '%s://%s:%s@%s:%s/%s' % (
    DBTYPE_POSTGRES, DB.user, quote_plus(DB.pass_), DB.host, DB.port, DB.name)

db_engine = create_engine(CORE_SQLALCHEMY_DATABASE_URI)

logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

DBBase = declarative_base()

# scoped_session should be strictly used where it is guaranteed that there would be use of single thread local like....
# .....in the case of celery
# but in cases of async stuff thread locals is not mapped to a single request , single request in fastapi can use.....
# ..... multiple thread locals or single thread local can handle multiple requests
# Also make sure you explicitly do db_session.remove() on teardown of the thread local
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=db_engine))


def get_db():
    """this function is used to inject db_session dependency in every rest api requests"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        # to be executed when request closes
        db.commit()
        db.close()


UTC = timezone('UTC')


def time_now():
    return datetime.now(UTC)
