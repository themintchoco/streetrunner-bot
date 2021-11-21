import os
import sys

import nextcord
import sentry_sdk

from bot.card.XPLevelUp import XPLevelUp
from bot.cogs.Admin import Admin
from bot.cogs.Leaderboard import Leaderboard
from bot.cogs.Player import Player
from bot.cogs.WebServer import WebServer
from bot.cogs.XP import XP
from bot.config import bot

BLACKLISTED_CHANNELS = [797035821630095393]
DEV_MODE = os.environ.get('DEV', None) == 'DEV'


async def process_xp(message):
    if not message.author.bot:
        level_before, level_after = await XP.process_message(message)
        if level_after > level_before:
            render = await XPLevelUp(message.author, level_before, level_after).render()
            await message.channel.send(file=nextcord.File(render.file_animated(format='GIF'), 'xp_levelup.gif'))


def is_xp_command(message):
    return message.startswith(f'{bot.command_prefix}xp') or (
            message.startswith(f'{bot.command_prefix}leaderboard') and message.endswith('xp'))


@bot.event
async def on_message(message):
    if message.channel.type != nextcord.ChannelType.text and DEV_MODE:
        # prevent development bot from replying to DMs
        return

    if message.guild and (message.guild.id == 846060357901615115) ^ DEV_MODE:
        # prevent production bot from replying to dev server and vice versa
        return

    if message.channel.id in BLACKLISTED_CHANNELS:
        return

    if is_xp_command(message.content.strip()):
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


def main():
    args = sys.argv[1:]
    try:
        test = args[0] == 'test'
    except IndexError:
        test = False

    if not test:
        sentry_sdk.init(
            'https://7b74da9447304a35b6f8c49da4fd09f1@o737869.ingest.sentry.io/5785215',
            traces_sample_rate=1.0,
        )

    bot.add_cog(Player(bot))
    bot.add_cog(XP(bot))
    bot.add_cog(Leaderboard(bot))
    bot.add_cog(Admin(bot))
    bot.add_cog(WebServer(bot))

    if not test:
        bot.run(os.environ['TOKEN'])


if __name__ == '__main__':
    main()
