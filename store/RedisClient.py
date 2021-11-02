import os

import aioredis

from helpers.utilities import SingletonBase


class RedisClient(SingletonBase):
    def __init__(self):
        if url := os.environ.get('REDIS_TLS_URL', False):
            self.pool = aioredis.from_url(url, ssl_cert_reqs=None)
        elif url := os.environ.get('REDIS_URL', False):
            self.pool = aioredis.from_url(url)
        else:
            raise RuntimeError()

    @property
    def conn(self):
        return self.pool
