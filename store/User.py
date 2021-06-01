from sqlalchemy import Column, Integer, BigInteger, DateTime
from sqlalchemy.orm import declarative_base, relationship


class User(declarative_base()):
	__tablename__ = 'discord_user'

	id = Column(BigInteger, primary_key=True)
	discord_id = Column(Integer)
	xp = Column(Integer)
	xp_refreshed = Column(DateTime)