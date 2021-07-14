import discord
from discord.ext import commands

from bot.card.Podium import *
from bot.card.TimeLeaderboard import TimeLeaderboard
from bot.card.XPLeaderboard import XPLeaderboard
from bot.exceptions import UsernameError, NotEnoughDataError


class Leaderboard(commands.Cog):
    """rank, blocks, infamy, kda, kills, deaths, time, xp"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def leaderboard(self, ctx):
        """Displays the current leaderboard!"""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                f'usage: {self.bot.command_prefix}{ctx.invoked_with} <rank|blocks|infamy|kda|kills|deaths|xp>')

    @leaderboard.command(name='rank')
    async def leaderboard_rank(self, ctx):
        """Displays the current leaderboard in terms of prison ranks"""
        async with ctx.typing():
            render = await RankPodium(discord_user=ctx.author).render()
        await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

    @leaderboard.command(name='blocks')
    async def leaderboard_blocks(self, ctx):
        """Displays the current leaderboard in terms of blocks mined"""
        async with ctx.typing():
            render = await BlocksPodium(discord_user=ctx.author).render()
        await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

    @leaderboard.command(name='infamy')
    async def leaderboard_infamy(self, ctx):
        """Displays the current leaderboard in terms of arena Infamy"""
        async with ctx.typing():
            render = await InfamyPodium(discord_user=ctx.author).render()
        await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

    @leaderboard.command(name='kda')
    async def leaderboard_kda(self, ctx):
        """Displays the current leaderboard in terms of arena KDA"""
        async with ctx.typing():
            render = await KdaPodium(discord_user=ctx.author).render()
        await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

    @leaderboard.command(name='kills')
    async def leaderboard_kills(self, ctx):
        """Displays the current leaderboard in terms of arena kills"""
        async with ctx.typing():
            render = await KillsPodium(discord_user=ctx.author).render()
        await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

    @leaderboard.command(name='deaths')
    async def leaderboard_deaths(self, ctx):
        """Displays the current leaderboard in terms of arena deaths"""
        async with ctx.typing():
            render = await DeathsPodium(discord_user=ctx.author).render()
        await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

    @leaderboard.command(name='time')
    async def leaderboard_time(self, ctx):
        """Displays the current leaderboard in terms of play time"""
        async with ctx.typing():
            render = await TimeLeaderboard(discord_user=ctx.author).render()
        await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

    @leaderboard.command(name='xp')
    async def leaderboard_xp(self, ctx):
        """Displays the current leaderboard in terms of discord XP"""
        async with ctx.typing():
            render = await XPLeaderboard(discord_user=ctx.author).render()
        await ctx.send(file=discord.File(render.file(format='PNG'), 'xp_leaderboard.png'))

    # @leaderboard.command(name='tournament')
    # async def leaderboard_tournament(self, ctx):
    #     """Displays the current tournament leaderboard! Fame and rewards await the top 10 players! """
    #     username = None
    #     async with ctx.typing():
    #         render = await event.render_event_leaderboard(discord_user=ctx.author)
    #         try:
    #             username = (await card.get_player_info(discord_user=ctx.author)).username
    #         except:
    #             pass
    #
    #     await ctx.send(file=discord.File(render.file(format='PNG'), 'tournament.png'))
    #     await ctx.send('View the full leaderboard LIVE at https://streetrunner.dev/tournament/'
    #                    + (f'?username={username}' if username else ''))

    @leaderboard.error
    @leaderboard_rank.error
    @leaderboard_blocks.error
    @leaderboard_infamy.error
    @leaderboard_kda.error
    @leaderboard_kills.error
    @leaderboard_deaths.error
    @leaderboard_time.error
    @leaderboard_xp.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, UsernameError):
                return await ctx.send(error.original.args[0]['message'])

            if isinstance(error.original, NotEnoughDataError):
                return await ctx.send(
                    f'There isn’t enough data to display the leaderboard at the moment. Please try again later!')

        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
        raise
