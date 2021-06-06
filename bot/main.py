import os

import discord
import sentry_sdk

from bot import card
from bot.Admin import Admin
from bot.Player import Player
from bot.WebServer import WebServer
from bot.XP import XP
from bot.config import bot

sentry_sdk.init(
    'https://7b74da9447304a35b6f8c49da4fd09f1@o737869.ingest.sentry.io/5785215',
    traces_sample_rate=1.0
)

bot.add_cog(Player(bot))
bot.add_cog(XP(bot))
bot.add_cog(Admin(bot))
bot.add_cog(WebServer(bot))


async def process_xp(message):
    if not message.author.bot:
        level_before, level_after = await XP.process_message(message)
        if level_after > level_before:
            render = await card.render_xp_levelup(message.author, level_before, level_after)
            await message.channel.send(file=discord.File(render.file_animated(format='GIF'), 'xp_levelup.gif'))


@bot.event
async def on_message(message):
    if message.guild and (message.guild.id == 846060357901615115) ^ (os.environ.get('DEV', False) == 'DEV'):
        # prevent production bot from replying to dev server and vice versa
        return

    if message.content.startswith(f'{bot.command_prefix}xp'):
        # exception for xp-related commands -- process xp before the command
        await process_xp(message)
        await bot.process_commands(message)
    else:
        await bot.process_commands(message)
        await process_xp(message)


@bot.event
async def on_error(event, *args, **kwargs):
    # allow Sentry to capture the error
    raise


bot.run(os.environ['TOKEN'])
