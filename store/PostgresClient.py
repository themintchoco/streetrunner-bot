import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from bot.utilities import Singleton


class PostgresClient(metaclass=Singleton):
    def __init__(self):
        uri = os.environ.get('DATABASE_URL')
        index_protocol = uri.index('://')

        self._uri = 'postgresql+asyncpg://' + uri[index_protocol + 3:]

    @property
    def session(self):
        return sessionmaker(bind=create_async_engine(self._uri, future=True), expire_on_commit=False,
                            class_=AsyncSession, future=True)
