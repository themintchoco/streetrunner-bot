import discord
from discord.ext import commands
from bot import card
import os
import datetime

from bot.card import CardType

PEDDLER_NAME = 'Luthor'
PEDDLER_AVATAR = 'images/peddler_avatar.png'


class Player(commands.Cog):
	"""rank, peddler"""
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=['prison'])
	async def rank(self, ctx, username: str):
		"""Displays player Prison stats"""
		image = await card.gen_card(username, CardType.Prison)
		await ctx.send(file=discord.File(image, 'rank_card.png'))

	@commands.command(aliases=['arena'])
	async def infamy(self, ctx, username: str):
		"""Displays player Arena stats"""
		image = await card.gen_card(username, CardType.Arena)
		await ctx.send(file=discord.File(image, 'rank_card.png'))

	@rank.error
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f'usage: {self.bot.command_prefix}{ctx.invoked_with} <Minecraft username>')
		elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, card.UsernameError):
			await ctx.send(f'That username appears to be invalid')
		else:
			await self.handle_command_error(ctx, error)

	@commands.command(aliases=['luthor'])
	async def peddler(self, ctx):
		"""Asks the mysterious peddler when he's leaving for his next destination"""
		for webhook in await ctx.channel.webhooks():
			if webhook.name == PEDDLER_NAME:
				return await self.handle_peddler(webhook)
		with open(PEDDLER_AVATAR, 'rb') as fp:
			return await self.handle_peddler(await ctx.channel.create_webhook(name=PEDDLER_NAME, avatar=fp.read()))

	async def handle_peddler(self, webhook):
		dt = datetime.datetime.utcnow()
		td = (datetime.datetime.min - dt) % datetime.timedelta(hours=8)
		td = (td // datetime.timedelta(minutes=5) + 1) * datetime.timedelta(minutes=5)

		if td <= datetime.timedelta(minutes=5):
			await webhook.send('I will be taking my leave soon')
		else:
			hours, minutes = td.seconds // 3600, (td.seconds // 60) % 60
			await webhook.send(f'I will leave for another mine in around {f"{hours} hours" if hours > 1 else "1 hour" if hours == 1 else ""}{" and " if hours > 0 and minutes > 0 else ""}{f"{minutes} minutes" if minutes > 0 else ""}. ')

	@peddler.error
	async def on_command_error(self, ctx, error):
		await self.handle_command_error(ctx, error)

	async def handle_command_error(self, ctx, error):
		await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
		raise