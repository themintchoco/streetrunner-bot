import discord
from discord.ext import commands

import os
from bot import card
from io import BytesIO

bot = commands.Bot(command_prefix='!')

@bot.command()
async def rank(ctx, username: str):
	image = await card.gen_card(username)

	fp = BytesIO()
	image.save(fp, format='PNG')
	fp.seek(0)

	await ctx.send(file=discord.File(fp, 'rank_card.png'))

@rank.error
async def on_command_error(ctx, error):
	print(error)
	if isinstance(error, MissingRequiredArgument):
		await ctx.send('gib username pls')
	else:
		await ctx.send(str(error))

bot.run(os.environ['TOKEN'])