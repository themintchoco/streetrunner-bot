import os
import discord
from discord.ext import commands
from bot.Player import Player
from bot.WebServer import WebServer
from pretty_help import PrettyHelp
import sentry_sdk

sentry_sdk.init(
    'https://7b74da9447304a35b6f8c49da4fd09f1@o737869.ingest.sentry.io/5785215',
    traces_sample_rate=1.0
)

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=PrettyHelp(no_category='Other'))

bot.add_cog(Player(bot))
bot.add_cog(WebServer(bot))

@bot.event
async def on_error(event, *args, **kwargs):
	# allow Sentry to capture the error
	raise

bot.run(os.environ['TOKEN'])