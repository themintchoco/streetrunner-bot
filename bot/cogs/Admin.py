import os

from discord.ext import commands

from bot.config import env


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator

    @commands.command(hidden=True)
    async def version(self, ctx):
        if 'HEROKU_APP_NAME' in os.environ:
            await ctx.send(f'{os.environ["HEROKU_APP_NAME"]} {os.environ["HEROKU_RELEASE_VERSION"]}')
        elif v := env.get('VERSION', None):
            await ctx.send(f'AWS {v}')
        else:
            await ctx.send('Local')

    @version.error
    async def on_command_error(self, ctx, error):
        await self.handle_command_error(ctx, error)

    async def handle_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have the permissions to use this command!')
        else:
            await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
            raise
