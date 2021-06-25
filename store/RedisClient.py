import os

import redis

from helpers.utilities import Singleton


class RedisClient(metaclass=Singleton):
    def __init__(self):
        self.pool = redis.from_url(os.environ.get('REDIS_TLS_URL'), ssl_cert_reqs=None)

    @property
    def conn(self):
        return self.pool
