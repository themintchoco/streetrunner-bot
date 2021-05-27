import discord
from discord.ext import commands
from bot import card
import os


class PlayerCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def rank(self, ctx, username: str):
		image = await card.gen_card(username)
		await ctx.send(file=discord.File(image, 'rank_card.png'))

	@rank.error
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f'usage: {self.bot.command_prefix}rank <Minecraft username>')
		else:
			await handle_command_error(ctx, error)

	async def handle_command_error(self, ctx, error):
		await ctx.send('Sorry, an error has occured. An admin will be notified. ')
		admin_user = self.bot.get_user(int(os.environ['ADMIN_USER_ID']))
		if admin_user:
			await admin_user.send(f'An error has occurred: {error}\nMessage: {ctx.message}')