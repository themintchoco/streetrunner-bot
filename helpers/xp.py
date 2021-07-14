import datetime

import discord
from sqlalchemy import select

from bot.api import get_chat_xp
from store.PostgresClient import PostgresClient
from store.User import User

def get_level_from_xp(xp: int) -> int:
    i = 1
    while True:
        if get_min_xp_for_level(i) > xp:
            return i - 1
        i += 1


def get_min_xp_for_level(level: int) -> int:
    if level > 0:
        return 20 * (level - 1) ** 2 + 35
    return 0


async def get_xp(discord_user: discord.User):
    async with PostgresClient().session() as session:
        user = (await session.execute(
            select(User)
                    .where(User.discord_id == discord_user.id)
        )).scalar()

        if not user:
            user = User(discord_id=discord_user.id,
                        xp=0,
                        xp_refreshed=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
            session.add(user)

        refresh_time = datetime.datetime.now(datetime.timezone.utc)

        xp_delta = (await get_chat_xp([user.discord_id], [(user.xp_refreshed, refresh_time)]))[0]
        if xp_delta is not None:
            user.xp += xp_delta
            user.xp_refreshed = refresh_time
            await session.commit()

        return user.xp


async def get_all_xp():
    async with PostgresClient().session() as session:
        users = (await session.execute(select(User))).scalars().all()

        refresh_time = datetime.datetime.now(datetime.timezone.utc)
        for i, xp_delta in enumerate(await get_chat_xp([user.discord_id for user in users],
                                                       [(user.xp_refreshed, refresh_time) for user in users])):
            if xp_delta is not None:
                users[i].xp += xp_delta
                users[i].xp_refreshed = refresh_time

        await session.commit()
        return users