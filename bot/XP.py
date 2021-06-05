import asyncio
import datetime

import discord
from discord.ext import commands
from sqlalchemy import select

from bot import card
from store.PostgresClient import PostgresClient
from store.User import User


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
