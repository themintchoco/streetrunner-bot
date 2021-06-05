from sqlalchemy import Column, Integer, BigInteger, DateTime
from sqlalchemy.orm import declarative_base


class User(declarative_base()):
    __tablename__ = 'discord_user'

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger)
    xp = Column(Integer)
    xp_refreshed = Column(DateTime(timezone=True))
