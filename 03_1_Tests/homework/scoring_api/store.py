import logging

from pymongo import MongoClient
from redis import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import TimeoutError
from redis.retry import Retry


DEFAULT_MONGODB_TIMEOUT = 2000
MONGODB_CONFIG = {
    'serverSelectionTimeoutMS': DEFAULT_MONGODB_TIMEOUT,
    'connectTimeoutMS': DEFAULT_MONGODB_TIMEOUT,
    'socketTimeoutMS': DEFAULT_MONGODB_TIMEOUT
}
MONGODB_DB = 'Otus'
MONGODB_COLLECTION = 'scoring_api'
REDIS_CONFIG = {
            'decode_responses': True,
            'socket_timeout': 2,
            'socket_connect_timeout': 2,
            'retry_on_timeout': True,
            'retry': Retry(ExponentialBackoff(), 3)
}


class MongoConnector:
    def __init__(self, config):
        self.storage = MongoClient(**config)[MONGODB_DB][MONGODB_COLLECTION]

    def get(self, key):
        result = self.storage.find_one({'_id': key})
        return result.get('value') if result else None


class RedisConnector:
    def __init__(self, config):
        self.storage = Redis(**config)

    def get(self, key):
        try:
            return self.storage.get(key)
        except TimeoutError:
            logging.error('Redis connection timeout')
            return None

    def set(self, key, value, expire_after=3600):
        try:
            self.storage.set(key, value, expire_after)
        except TimeoutError:
            logging.error('Redis connection timeout')


class DBConnector:
    def __init__(self):
        self.mongodb_storage = MongoConnector(MONGODB_CONFIG)
        self.redis_storage = RedisConnector(REDIS_CONFIG)

    def get(self, key):
        self.mongodb_storage.get(key)

    def cache_set(self, key, value, expire_after=3600):
        self.redis_storage.set(key, value, expire_after)

    def cache_get(self, key):
        result = self.redis_storage.get(key)
        if result:
            return result
        else:
            # looking for data in main database
            mongo_result = self.mongodb_storage.get(key)
            if mongo_result:
                # storing value in buffer database (Redis)
                self.cache_set(key, mongo_result)
                return mongo_result
