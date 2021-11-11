import json
import os

import nextcord
from nextcord.ext import commands
from pretty_help import PrettyHelp

env = {}

if os.path.isfile('env.json'):
    with open('env.json') as f:
        env = json.loads(f.read())

intents = nextcord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!',
                   intents=intents,
                   help_command=PrettyHelp(no_category='Other'),
                   activity=nextcord.Game('mc.streetrunner.gg | !help'))
