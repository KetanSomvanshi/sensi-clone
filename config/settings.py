from dotenv import load_dotenv

from config.util import Environment
from logger import logger

# Load env variables from a file, if exists else default would be set
logger.info("SERVER_INIT::Setting environment variables from .env file(if exists)...")
load_dotenv(verbose=True)


class DB:
    host = Environment.get_string("DB_HOST", "postgres_db")
    port = Environment.get_string("DB_PORT", '5432')
    name = Environment.get_string("DB_NAME", "sensi")
    user = Environment.get_string("DB_USER", "ketansomvanshi")
    pass_ = Environment.get_string("DB_PASS", "zxcvbnml")


class CELERY:
    broker_uri = Environment.get_string("CELERY_BROKER_URI", "redis://redis_server:6379/1")


class REDIS:
    url = Environment.get_string("REDIS_URL", "redis://redis_server:6379/0")


class BrokerConfig:
    url = Environment.get_string("BROKER_INTEGRATION_URL", "https://prototype.sbulltech.com/api")
    underlying_url = Environment.get_string("BROKER_UNDERLYING_URL", "/underlyings")
    derivative_url = Environment.get_string("BROKER_DERIVATIVE_URL", "/derivatives/%s")
