import discord
from discord.ext import commands
from pretty_help import PrettyHelp

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!',
                   intents=intents,
                   help_command=PrettyHelp(no_category='Other'),
                   activity=discord.Game('mc.streetrunner.dev | !help'))
