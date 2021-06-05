import asyncio
import datetime
import os
from typing import List, Tuple

import aiohttp
import discord
from discord.ext import commands
from sqlalchemy import select

from bot import card
from store.PostgresClient import PostgresClient
from store.User import User


async def get_chat_xp(discord_id: List[int], timerange: List[Tuple[datetime.datetime, datetime.datetime]]) -> List[int]:
    query = {'data': [{
        'discord_id': str(discord_id[i]),
        'start': int(timerange[i][0].timestamp()),
        'end': int(timerange[i][1].timestamp())
    } for i in range(len(discord_id))],
        'cooldown': 8}

    async with aiohttp.ClientSession() as s:
        async with s.post(
                f'https://streetrunner.dev/api/chat/', json=query,
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status != 200:
                print(await r.text())
                raise

            return await r.json()


class XP(commands.Cog):
    xp_cooldown = {}

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def process_message(message):
        if message.author.id in XP.xp_cooldown:
            return

        XP.xp_cooldown[message.author.id] = True

        async with PostgresClient().session() as session:
            user = (await session.execute(
                select(User)
                    .where(User.discord_id == message.author.id)
            )).scalar()

            if not user:
                user = User(discord_id=message.author.id,
                            xp=0,
                            xp_refreshed=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
                session.add(user)

            user.xp += 1
            await session.commit()

        await asyncio.sleep(8)
        XP.xp_cooldown.pop(message.author.id, None)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def get_level_from_xp(xp: int) -> int:
        i = 1
        while True:
            if XP.get_min_xp_for_level(i) > xp:
                return i - 1
            i += 1

    @staticmethod
    def get_min_xp_for_level(level: int) -> int:
        if level > 0:
            return 20 * (level - 1) ** 2 + 35
        return 0

    @commands.group()
    async def xp(self, ctx):
        if ctx.invoked_subcommand is None:
            async with ctx.typing():
                render = await card.render_xp_card(discord_user=ctx.author)

            if render.multi_frame:
                await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'xp.gif'))
            else:
                await ctx.send(file=discord.File(render.file(format='PNG'), 'xp.png'))

    @xp.command(name='leaderboard')
    async def xp_leaderboard(self, ctx):
        async with ctx.typing():
            render = await card.render_xp_leaderboard(discord_user=ctx.author)

        await ctx.send(file=discord.File(render.file(format='PNG'), 'xp_leaderboard.png'))

    @xp.error
    @xp_leaderboard.error
    async def on_command_error(self, ctx, error):
        await self.handle_command_error(ctx, error)

    @xp.group(name='give')
    @commands.has_permissions(administrator=True)
    async def xp_give(self, ctx, target_user: discord.User, xp: int):
        async with PostgresClient().session() as session:
            user = (await session.execute(
                select(User)
                    .where(User.discord_id == target_user.id)
            )).scalar()

            if not user:
                user = User(discord_id=target_user.id,
                            xp=0,
                            xp_refreshed=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
                session.add(user)

            user.xp += xp
            await session.commit()

    @xp_give.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                f'usage: {self.bot.command_prefix}{" ".join(ctx.invoked_parents)} {ctx.invoked_with} <user> <amount>')
        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'You do not have the permissions to use this command!')
        else:
            await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
            raise
