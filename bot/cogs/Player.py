import typing

import discord
from aiohttp import ClientResponseError
from discord.ext import commands

from bot.api import StreetRunnerApi
from bot.card.PlayerCard import DeathsCard, InfamyCard, KdaCard, KillsCard, PlayerCard, RankCard, TimeCard
from bot.exceptions import APIError, DiscordNotLinkedError, UsernameError
from bot.player.privacy import Privacy


class Player(commands.Cog):
    """rank, infamy, kills, kda, deaths, time"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['prison'])
    async def rank(self, ctx, user: typing.Optional[typing.Union[discord.Member, str]]):
        """Displays player Prison stats"""
        await self.respond_card(ctx, RankCard, user, Privacy.prison)

    @commands.command(aliases=['arena'])
    async def infamy(self, ctx, user: typing.Optional[typing.Union[discord.Member, str]]):
        """Displays player Arena stats"""
        await self.respond_card(ctx, InfamyCard, user, Privacy.arena)

    @commands.command()
    async def kills(self, ctx, user: typing.Optional[typing.Union[discord.Member, str]]):
        """Displays player Arena kill stats"""
        await self.respond_card(ctx, KillsCard, user, Privacy.arena)

    @commands.command()
    async def kda(self, ctx, user: typing.Optional[typing.Union[discord.Member, str]]):
        """Displays player Arena kda stats"""
        await self.respond_card(ctx, KdaCard, user, Privacy.arena)

    @commands.command()
    async def deaths(self, ctx, user: typing.Optional[typing.Union[discord.Member, str]]):
        """Displays player Arena death stats"""
        await self.respond_card(ctx, DeathsCard, user, Privacy.arena)

    @commands.command()
    async def time(self, ctx, user: typing.Optional[typing.Union[discord.Member, str]]):
        """Displays player time"""
        await self.respond_card(ctx, TimeCard, user, Privacy.time)

    async def respond_card(self, ctx, card_type: PlayerCard, user, privacy_mask: Privacy = 0):
        if user is None:
            username = None
            user = ctx.author
        elif isinstance(user, str):
            username = user
            user = ctx.author
        else:
            username = None

        player = StreetRunnerApi.Player.Player({'mc_username': username, 'discord_id': user.id})
        target = ctx

        try:
            if (await player.PlayerPrivacy().data).value & privacy_mask:
                username = username or (await player.PlayerInfo().data).name

                if (target := user) == ctx.author:
                    await ctx.send('Sent to your DMs due to your privacy settings.')
                else:
                    await ctx.send(f'Due to {username}’s privacy settings, stats cannot be shown.')
                    return

        except ClientResponseError as e:
            if e.status == 404:
                if username:
                    raise UsernameError(username)
                else:
                    raise DiscordNotLinkedError(user.id)

            raise APIError(e)

        async with target.typing():
            render = await card_type(username=username, discord_user=user).render()

        if render.multi_frame:
            await target.send(file=discord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await target.send(file=discord.File(render.file('PNG'), 'player_card.png'))

    @rank.error
    @infamy.error
    @kills.error
    @kda.error
    @deaths.error
    @time.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, UsernameError):
            return await ctx.send(error.original, allowed_mentions=discord.AllowedMentions.none())

        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
        raise
