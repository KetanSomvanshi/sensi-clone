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
    trigger_freqn_for_derivative = Environment.get_int("CELERY_TRIGGER_FREQN_FOR_DERIVATIVE", 60)
    trigger_freqn_for_underlying = Environment.get_int("CELERY_TRIGGER_FREQN_FOR_UNDERLYING", 300)


class REDIS:
    url = Environment.get_string("REDIS_URL", "redis://redis_server:6379/0")


class BrokerConfig:
    url = Environment.get_string("BROKER_INTEGRATION_URL", "https://prototype.sbulltech.com/api")
    underlying_url = Environment.get_string("BROKER_UNDERLYING_URL", "/underlyings")
    derivative_url = Environment.get_string("BROKER_DERIVATIVE_URL", "/derivatives/{}")
    ws_url = Environment.get_string("BROKER_WS_URL", "wss://prototype.sbulltech.com/api/ws")
