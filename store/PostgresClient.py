import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from helpers.utilities import Singleton


class PostgresClient(metaclass=Singleton):
    def __init__(self):
        uri = os.environ.get('DATABASE_URL')
        index_protocol = uri.index('://')

        self._uri = 'postgresql+asyncpg://' + uri[index_protocol + 3:]
        self._engine = create_async_engine(self._uri, poolclass=NullPool, future=True)

    @property
    def session(self):
        return sessionmaker(bind=self._engine, expire_on_commit=False, class_=AsyncSession, future=True)
