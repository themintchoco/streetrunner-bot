import datetime
import typing

import discord
from discord.ext import commands

from bot.card.PlayerCard import DeathsCard, InfamyCard, KdaCard, KillsCard, RankCard, TimeCard
from bot.exceptions import UsernameError


class Player(commands.Cog):
    """rank, infamy, kills, kda, deaths, time"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['prison'])
    async def rank(self, ctx, obj: typing.Union[discord.Member, str]):
        """Displays player Prison stats"""
        async with ctx.typing():
            is_string = isinstance(obj, str)
            render = await RankCard(username=obj if is_string else None,
                                    discord_user=ctx.author if is_string else obj).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command(aliases=['arena'])
    async def infamy(self, ctx, obj: typing.Union[discord.Member, str]):
        """Displays player Arena stats"""
        async with ctx.typing():
            is_string = isinstance(obj, str)
            render = await InfamyCard(username=obj if is_string else None,
                                      discord_user=ctx.author if is_string else obj).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def kills(self, ctx, obj: typing.Union[discord.Member, str]):
        """Displays player Arena kill stats"""
        async with ctx.typing():
            is_string = isinstance(obj, str)
            render = await KillsCard(username=obj if is_string else None,
                                     discord_user=ctx.author if is_string else obj).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def kda(self, ctx, obj: typing.Union[discord.Member, str]):
        """Displays player Arena kda stats"""
        async with ctx.typing():
            is_string = isinstance(obj, str)
            render = await KdaCard(username=obj if is_string else None,
                                   discord_user=ctx.author if is_string else obj).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def deaths(self, ctx, obj: typing.Union[discord.Member, str]):
        """Displays player Arena death stats"""
        async with ctx.typing():
            is_string = isinstance(obj, str)
            render = await DeathsCard(username=obj if is_string else None,
                                      discord_user=ctx.author if is_string else obj).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def time(self, ctx, obj: typing.Union[discord.Member, str]):
        """Displays player time"""
        async with ctx.typing():
            is_string = isinstance(obj, str)
            render = await TimeCard(username=obj if is_string else None,
                                    discord_user=ctx.author if is_string else obj).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @rank.error
    @infamy.error
    @kills.error
    @kda.error
    @deaths.error
    @time.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, UsernameError):
            return await ctx.send(error.original.args[0]['message'])

        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
        raise
