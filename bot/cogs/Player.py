import re

import nextcord
from nextcord.ext import commands

from bot.api import StreetRunnerApi
from bot.card.BalanceCard import BalanceCard
from bot.card.PlayerCard import PlayerCard
from bot.card.StatsCard import DeathsCard, InfamyCard, KdaCard, KillsCard, RankCard, TimeCard, WikiCard
from bot.cogs.cogs import PlayerRespondMixin, PlayerRespondType
from bot.exceptions import PrivacyError, UsernameError
from bot.player.privacy import Privacy
from bot.view.PrivacyOptionsView import PrivacyOptionsView


class Player(commands.Cog, PlayerRespondMixin):
    """rank, infamy, kills, kda, deaths, time"""

    privacy_user_message_map = {}

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['prison'])
    async def rank(self, ctx, username: str = None):
        """Displays player Prison stats"""
        await self.respond_card(ctx, RankCard, username, Privacy.prison)

    @commands.command(aliases=['arena'])
    async def infamy(self, ctx, username: str = None):
        """Displays player Arena stats"""
        await self.respond_card(ctx, InfamyCard, username, Privacy.arena)

    @commands.command()
    async def kills(self, ctx, username: str = None):
        """Displays player Arena kill stats"""
        await self.respond_card(ctx, KillsCard, username, Privacy.arena)

    @commands.command()
    async def kda(self, ctx, username: str = None):
        """Displays player Arena kda stats"""
        await self.respond_card(ctx, KdaCard, username, Privacy.arena)

    @commands.command()
    async def deaths(self, ctx, username: str = None):
        """Displays player Arena death stats"""
        await self.respond_card(ctx, DeathsCard, username, Privacy.arena)

    @commands.command()
    async def time(self, ctx, username: str = None):
        """Displays player time"""
        await self.respond_card(ctx, TimeCard, username, Privacy.time)

    @commands.command()
    async def wiki(self, ctx, username: str = None):
        """Displays player wiki points"""
        await self.respond_card(ctx, WikiCard, username)

    @commands.command()
    async def balance(self, ctx, username: str = None):
        """Displays player balance"""
        await self.respond_card(ctx, BalanceCard, username, Privacy.balance)

    async def respond_card(self, ctx, card_type: PlayerCard, username, privacy: Privacy = 0):
        user = ctx.author

        try:
            if username and (match := re.match(r'<@!?(\d+?)>', username)):
                if not (user := self.bot.get_user(int(match.group(1)))):
                    raise UsernameError()
                username = None
        except ValueError:
            raise UsernameError()

        async with ctx.typing():
            player = StreetRunnerApi.Player.Player({'mc_username': username, 'discord_id': user.id})
            render = await card_type(username=username, discord_user=user, privacy=privacy).render()

        try:
            if render.animated:
                file = nextcord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif')
            else:
                file = nextcord.File(render.file('PNG'), 'player_card.png')

            if (await self.respond(ctx, player, privacy, file=file) == PlayerRespondType.DM
                    and ctx.channel.type == nextcord.ChannelType.text):
                await ctx.send('Sent to your DMs due to your privacy settings.')

        except PrivacyError as e:
            await ctx.send(f'Due to {e.args[0].name}’s privacy settings, stats cannot be shown.')

        except nextcord.errors.Forbidden:
            await ctx.send('DM cannot be sent. Please check your Discord settings and ensure that server members can '
                           'send you DMs. Alternatively, disable Privacy to allow responses to be sent here. ')

    @commands.command()
    async def privacy(self, ctx):
        """Adjust privacy settings"""
        async with ctx.typing():
            if message := self.privacy_user_message_map.get(ctx.author.id):
                await message.delete()

            privacy = (await StreetRunnerApi.Player.Player({'discord_id': ctx.author.id}).PlayerPrivacy().data).value

            self.privacy_user_message_map[ctx.author.id] = await ctx.send(
                embed=nextcord.Embed(
                    title=f'Privacy settings for {ctx.author.display_name}',
                    description='When Privacy is enabled, personal responses that fall in the selected categories '
                                'will be sent to your DMs instead. You will also not appear in leaderboards for the categories '
                                'selected. '
                ),
                view=PrivacyOptionsView(user=ctx.author, privacy=privacy),
            )

    @rank.error
    @infamy.error
    @kills.error
    @kda.error
    @deaths.error
    @time.error
    @wiki.error
    @balance.error
    @privacy.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, UsernameError):
            return await ctx.send(error.original.args[0]['message'], allowed_mentions=nextcord.AllowedMentions.none())

        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
        raise
