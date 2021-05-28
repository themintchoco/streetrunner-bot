import os
import redis


class Singleton(type):
	_instances = {}

	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]


class RedisClient(metaclass=Singleton):
	def __init__(self):
		self.pool = redis.ConnectionPool.from_url(os.environ.get("REDIS_TLS_URL"), ssl_cert_reqs=None)

	@property
	def conn(self):
		if not hasattr(self, '_conn'):
			self.getConnection()
		return self._conn

	def getConnection(self):
		self._conn = redis.Redis(connection_pool=self.pool)
