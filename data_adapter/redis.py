from typing import List, Dict, Set

from redis import Redis

from config.settings import REDIS
from controller.context_manager import context_log_meta
from logger import logger
from utils.utils import Singleton


@Singleton
class Cache:
    def __init__(self):
        self.__redis_url = REDIS.url
        self._redis = self.__init_redis()

    def __init_redis(self):
        try:
            redis = Redis.from_url(
                self.__redis_url, encoding="utf-8", decode_responses=True)
        except Exception as e:
            logger.error(f"error in initiating redis in non cluster mode for url : {self.__redis_url} error : {e}")
            return None
        return redis

    def __validate(self, key='default_valid') -> bool:
        if not (self._redis and key):
            return False
        return True

    def sadd(self, key: str, values: List[str]) -> int:
        try:
            if not self.__validate(key=key):
                return 0
            return self._redis.sadd(key, *values)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"error in redis sadd : {e}")
            return 0

    def smembers(self, key: str) -> Set[str]:
        try:
            if not self.__validate(key=key):
                return set()
            return set(self._redis.smembers(key))
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"error in redis smembers : {e}")
            return set()

    def hset(self, key: str, mapping: dict) -> bool:
        try:
            if not self.__validate(key=key):
                return False
            return self._redis.hset(name=key, mapping=mapping)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"error in redis hset : {e}")
            return False

    def hgetall(self, key: str) -> dict:
        try:
            if not self.__validate(key=key):
                return {}
            return self._redis.hgetall(key)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"error in redis hgetall : {e}")
            return {}

    def hkeys(self, key: str) -> List[str]:
        try:
            if not self.__validate(key=key):
                return []
            return self._redis.hkeys(key)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"error in redis hkeys : {e}")
            return []
