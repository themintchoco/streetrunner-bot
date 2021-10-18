import json
import os

import discord
from discord.ext import commands
from pretty_help import PrettyHelp

env = {}

if os.path.isfile('env.json'):
    with open('env.json') as f:
        env = json.loads(f.read())

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!',
                   intents=intents,
                   help_command=PrettyHelp(no_category='Other'),
                   activity=discord.Game('mc.streetrunner.gg | !help'))
