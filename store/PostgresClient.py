import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from bot.utilities import Singleton


class PostgresClient(metaclass=Singleton):
	def __init__(self):
		uri = os.environ.get('DATABASE_URL')
		if uri.startswith('postgres://'):
			uri = uri.replace('postgres://', 'postgresql://', 1)

		session_factory = sessionmaker(bind=create_engine(uri, future=True), future=True)
		self.session = scoped_session(session_factory)
