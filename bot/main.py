import discord
from discord.ext import commands

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
	await ctx.send('gib username pls')

bot.run(os.environ['TOKEN'])