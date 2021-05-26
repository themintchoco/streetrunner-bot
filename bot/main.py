import os
import discord
from discord.ext import commands
from bot.PlayerCog import PlayerCog
from bot.WebServerCog import WebServerCog


intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

bot.add_cog(PlayerCog(bot))
bot.add_cog(WebServerCog(bot))

bot.run(os.environ['TOKEN'])