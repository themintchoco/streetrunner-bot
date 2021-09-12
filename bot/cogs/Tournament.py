import discord
from discord.ext import commands

from bot.card.Tournament import TournamentPodium
from bot.exceptions import UsernameError


class Tournament(commands.Cog):
    """Display the tournament leaderboard!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tournament(self, ctx, username: str = None):
        """Displays tournament leaderboard"""
        async with ctx.typing():
            render = await TournamentPodium(username=username, discord_user=ctx.author).render()

        await ctx.send(file=discord.File(render.file('PNG'), 'tournament_leaderboard.png'))

    @tournament.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, UsernameError):
            return await ctx.send(error.original.args[0]['message'])

        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
        raise
