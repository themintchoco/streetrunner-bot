import typing

import nextcord
from nextcord.ext import commands

from bot.api import StreetRunnerApi
from bot.card.PlayerCard import DeathsCard, InfamyCard, KdaCard, KillsCard, PlayerCard, RankCard, TimeCard, WikiCard
from bot.exceptions import APIError, DiscordNotLinkedError, UsernameError
from bot.player.privacy import Privacy
from bot.view.PrivacyOptionsView import PrivacyOptionsView


class Player(commands.Cog):
    """rank, infamy, kills, kda, deaths, time"""

    privacy_user_message_map = {}

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['prison'])
    async def rank(self, ctx, user: typing.Optional[typing.Union[nextcord.Member, str]]):
        """Displays player Prison stats"""
        await self.respond_card(ctx, RankCard, user, Privacy.prison)

    @commands.command(aliases=['arena'])
    async def infamy(self, ctx, user: typing.Optional[typing.Union[nextcord.Member, str]]):
        """Displays player Arena stats"""
        await self.respond_card(ctx, InfamyCard, user, Privacy.arena)

    @commands.command()
    async def kills(self, ctx, user: typing.Optional[typing.Union[nextcord.Member, str]]):
        """Displays player Arena kill stats"""
        await self.respond_card(ctx, KillsCard, user, Privacy.arena)

    @commands.command()
    async def kda(self, ctx, user: typing.Optional[typing.Union[nextcord.Member, str]]):
        """Displays player Arena kda stats"""
        await self.respond_card(ctx, KdaCard, user, Privacy.arena)

    @commands.command()
    async def deaths(self, ctx, user: typing.Optional[typing.Union[nextcord.Member, str]]):
        """Displays player Arena death stats"""
        await self.respond_card(ctx, DeathsCard, user, Privacy.arena)

    @commands.command()
    async def time(self, ctx, user: typing.Optional[typing.Union[nextcord.Member, str]]):
        """Displays player time"""
        await self.respond_card(ctx, TimeCard, user, Privacy.time)
        
    @commands.command()
    async def wiki(self, ctx, user: typing.Optional[typing.Union[nextcord.Member, str]]):
        """Displays player wiki points"""
        await self.respond_card(ctx, WikiCard, user)

    async def respond_card(self, ctx, card_type: PlayerCard, user, privacy_mask: Privacy = 0):
        if user is None:
            username = None
            user = ctx.author
        elif isinstance(user, str):
            username = user
            user = ctx.author
        else:
            username = None

        async with ctx.typing():
            player = StreetRunnerApi.Player.Player({'mc_username': username, 'discord_id': user.id})
            target = ctx

            try:
                if (await player.PlayerPrivacy().data).value & privacy_mask:
                    player_info = await player.PlayerInfo().data

                    if (target := self.bot.get_user(player_info.discord)) == ctx.author:
                        await ctx.send('Sent to your DMs due to your privacy settings.')
                    else:
                        await ctx.send(f'Due to {player_info.username}’s privacy settings, stats cannot be shown.')
                        return

            except APIError as e:
                if e.status == 404:
                    if username:
                        raise UsernameError(username)
                    else:
                        raise DiscordNotLinkedError(user.id)

                raise

        async with target.typing():
            render = await card_type(username=username, discord_user=user).render()

        if render.multi_frame:
            await target.send(file=nextcord.File(render.file_animated(format='GIF', loop=0), 'player_card.gif'))
        else:
            await target.send(file=nextcord.File(render.file('PNG'), 'player_card.png'))

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
    @privacy.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, UsernameError):
            return await ctx.send(error.original.args[0]['message'], allowed_mentions=nextcord.AllowedMentions.none())

        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
        raise
