import datetime

import discord
from discord.ext import commands

from bot.card.PlayerCard import DeathsCard, InfamyCard, KdaCard, KillsCard, RankCard, TimeCard
from bot.exceptions import UsernameError

class Player(commands.Cog):
    """rank, infamy, kills, kda, deaths, time, peddler"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['prison'])
    async def rank(self, ctx, username: str = None):
        """Displays player Prison stats"""
        async with ctx.typing():
            render = await RankCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command(aliases=['arena'])
    async def infamy(self, ctx, username: str = None):
        """Displays player Arena stats"""
        async with ctx.typing():
            render = await InfamyCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def kills(self, ctx, username: str = None):
        """Displays player Arena kill stats"""
        async with ctx.typing():
            render = await KillsCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def kda(self, ctx, username: str = None):
        """Displays player Arena kda stats"""
        async with ctx.typing():
            render = await KdaCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def deaths(self, ctx, username: str = None):
        """Displays player Arena death stats"""
        async with ctx.typing():
            render = await DeathsCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def time(self, ctx, username: str = None):
        """Displays player time"""
        async with ctx.typing():
            render = await TimeCard(username=username, discord_user=ctx.author).render()

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
