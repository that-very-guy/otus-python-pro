import logging

from pymongo import MongoClient
from redis import Redis
from redis.backoff import ExponentialBackoff
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


class DBConnector:
    def __init__(self):
        self.mongodb_storage = MongoClient(**MONGODB_CONFIG)[MONGODB_DB][MONGODB_COLLECTION]
        self.redis_storage = Redis(**REDIS_CONFIG)

    def get(self, key):
        result = self.mongodb_storage.find_one({'_id': key})
        return result.get('value') if result else None

    def cache_set(self, key, value, expire_after=3600):
        try:
            self.redis_storage.set(key, value, expire_after)
        except Exception as e:
            logging.error(e)

    def cache_get(self, key):
        result = self.redis_storage.get(key)
        if result:
            return result
        else:
            # looking for data in main database
            mongo_result = self.mongodb_storage.find_one({'_id': key})
            if mongo_result:
                result = mongo_result.get('value')
                # storing value in buffer database (Redis)
                self.cache_set(key, result)
                return result
