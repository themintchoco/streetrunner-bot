import discord
from discord.ext import commands
from bot import card


class PlayerCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def rank(self, ctx, username: str):
		image = await card.gen_card(username)
		await ctx.send(file=discord.File(image, 'rank_card.png'))

	@rank.error
	async def on_command_error(self, ctx, error):
		print(error)
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send('gib username pls')
		else:
			await ctx.send(str(error))