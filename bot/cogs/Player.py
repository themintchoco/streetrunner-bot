import datetime

import discord
from discord.ext import commands

from bot.card.PlayerCard import DeathsCard, InfamyCard, KdaCard, KillsCard, RankCard, TimeCard
from bot.exceptions import UsernameError

PEDDLER_NAME = 'Luthor'
PEDDLER_AVATAR = 'images/peddler_avatar.png'


class Player(commands.Cog):
    """rank, infamy, kills, kda, deaths, time, peddler"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['prison'])
    async def rank(self, ctx, username: str = None):
        """Displays player Prison stats"""
        render = await RankCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command(aliases=['arena'])
    async def infamy(self, ctx, username: str = None):
        """Displays player Arena stats"""
        render = await InfamyCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def kills(self, ctx, username: str = None):
        """Displays player Arena kill stats"""
        render = await KillsCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def kda(self, ctx, username: str = None):
        """Displays player Arena kda stats"""
        render = await KdaCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def deaths(self, ctx, username: str = None):
        """Displays player Arena death stats"""
        render = await DeathsCard(username=username, discord_user=ctx.author).render()

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def time(self, ctx, username: str = None):
        """Displays player time"""
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

    @commands.command(aliases=['luthor'])
    async def peddler(self, ctx):
        """Asks the mysterious peddler when he's leaving for his next destination"""
        for webhook in await ctx.channel.webhooks():
            if webhook.name == PEDDLER_NAME:
                return await self.handle_peddler(webhook)
        with open(PEDDLER_AVATAR, 'rb') as fp:
            return await self.handle_peddler(await ctx.channel.create_webhook(name=PEDDLER_NAME, avatar=fp.read()))

    async def handle_peddler(self, webhook):
        dt = datetime.datetime.utcnow()
        td = (datetime.datetime.min - dt) % datetime.timedelta(hours=8)
        td = (td // datetime.timedelta(minutes=5) + 1) * datetime.timedelta(minutes=5)

        if td == datetime.timedelta(hours=8):
            await webhook.send('I will be taking my leave soon')
        else:
            hours, minutes = td.seconds // 3600, (td.seconds // 60) % 60
            await webhook.send('I will leave for another mine in around {}{}{}. '.format(
                f'{hours} hours' if hours > 1 else '1 hour' if hours == 1 else '',
                ' and ' if hours > 0 and minutes > 0 else '',
                f'{minutes} minutes' if minutes > 0 else '',
            ))

    @peddler.error
    async def on_peddler_command_error(self, ctx, error):
        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
        raise
