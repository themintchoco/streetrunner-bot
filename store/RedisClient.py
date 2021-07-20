import os

import redis

from helpers.utilities import Singleton


class RedisClient(metaclass=Singleton):
    def __init__(self):
        self.pool = redis.from_url(os.environ.get('REDIS_URL'))

    @property
    def conn(self):
        return self.pool
