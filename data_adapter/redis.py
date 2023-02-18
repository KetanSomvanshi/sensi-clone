from typing import List, Dict, Set

from redis import Redis

from config.settings import REDIS
from controller.context_manager import context_log_meta
from logger import logger
from utils.utils import Singleton


@Singleton
class Cache:
    """abstract layer for redis, using singleton pattern here to avoid multiple connections"""

    def __init__(self):
        """initiate redis connection and pubsub connection"""
        self.__redis_url = REDIS.url
        self._redis = self.__init_redis()
        self._pubsub = self._redis.pubsub()

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

    def sadd_and_publish(self, topic: str, msg: str, key: str, values: List[str]) -> int:
        """add data to set and publish on given topic"""
        try:
            if not self.__validate(key=key):
                return 0
            pipeline = self._redis.pipeline()
            pipeline.sadd(key, *values)
            pipeline.publish(topic, msg)
            return pipeline.execute()[0]
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"error in redis sadd_and_publish : {e}")
            return 0

    def smembers_and_delete(self, key: str) -> Set[str]:
        """get smembers and delete key"""
        try:
            if not self.__validate(key=key):
                return set()
            pipeline = self._redis.pipeline()
            pipeline.smembers(key)
            pipeline.delete(key)
            return set(pipeline.execute()[0])
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"error in redis smembers_and_delete : {e}")
            return set()

    def subscribe(self, topic: str) -> None:
        """subscribe to given topic"""
        try:
            if not self.__validate():
                return
            self._pubsub.subscribe(topic)
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"error in redis subscribe : {e}")
            return

    def get_message(self) -> Dict:
        """get message from given topic"""
        try:
            if not self.__validate():
                return {}
            return self._pubsub.get_message()
        except Exception as e:
            logger.error(extra=context_log_meta.get(), msg=f"error in redis get_message : {e}")
            return {}
