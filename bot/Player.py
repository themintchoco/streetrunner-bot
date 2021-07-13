import datetime

import discord
from discord.ext import commands

from bot import card
from bot.card import CardType
from bot.exceptions import UsernameError, NotEnoughDataError

PEDDLER_NAME = 'Luthor'
PEDDLER_AVATAR = 'images/peddler_avatar.png'


class Player(commands.Cog):
    """rank, infamy, kills, kda, deaths, time, peddler"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['prison'])
    async def rank(self, ctx, username: str = None):
        """Displays player Prison stats"""
        render = await (
            card.render_player_card(username=username, type=CardType.Prison) if username else
            card.render_player_card(discord_user=ctx.author, type=CardType.Prison))

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command(aliases=['arena'])
    async def infamy(self, ctx, username: str = None):
        """Displays player Arena stats"""
        render = await (
            card.render_player_card(username=username, type=CardType.Infamy) if username else
            card.render_player_card(discord_user=ctx.author, type=CardType.Infamy))

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def kills(self, ctx, username: str = None):
        """Displays player Arena kill stats"""
        render = await (
            card.render_player_card(username=username, type=CardType.Kills) if username else
            card.render_player_card(discord_user=ctx.author, type=CardType.Kills))

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def kda(self, ctx, username: str = None):
        """Displays player Arena kda stats"""
        render = await (
            card.render_player_card(username=username, type=CardType.Kda) if username else
            card.render_player_card(discord_user=ctx.author, type=CardType.Kda))

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def deaths(self, ctx, username: str = None):
        """Displays player Arena death stats"""
        render = await (
            card.render_player_card(username=username, type=CardType.Deaths) if username else
            card.render_player_card(discord_user=ctx.author, type=CardType.Deaths))

        if render.multi_frame:
            await ctx.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @commands.command()
    async def time(self, ctx, username: str = None):
        """Displays player time"""
        render = await (
            card.render_player_card(username=username, type=CardType.Time) if username else
            card.render_player_card(discord_user=ctx.author, type=CardType.Time))

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
            await webhook.send(
                f'I will leave for another mine in around {f"{hours} hours" if hours > 1 else "1 hour" if hours == 1 else ""}{" and " if hours > 0 and minutes > 0 else ""}{f"{minutes} minutes" if minutes > 0 else ""}. ')

    @peddler.error
    async def on_command_error(self, ctx, error):
        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
        raise
