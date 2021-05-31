import datetime

import discord
from discord.ext import commands

from bot import card
from bot.card import CardType

PEDDLER_NAME = 'Luthor'
PEDDLER_AVATAR = 'images/peddler_avatar.png'


class Player(commands.Cog):
	"""rank, infamy, kills, leaderboard, peddler"""

	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=['prison'])
	async def rank(self, ctx, username: str = None):
		"""Displays player Prison stats"""
		render = await (card.render_card(username=username, type=CardType.Prison) if username else card.render_card(
			discord_user=ctx.author, type=CardType.Prison))
		await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

	@commands.command(aliases=['arena'])
	async def infamy(self, ctx, username: str = None):
		"""Displays player Arena stats"""
		render = await (card.render_card(username=username, type=CardType.Infamy) if username else card.render_card(
			discord_user=ctx.author, type=CardType.Infamy))
		await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

	@commands.command(aliases=['kda'])
	async def kills(self, ctx, username: str = None):
		"""Displays player Arena kill stats"""
		render = await (card.render_card(username=username, type=CardType.Kills) if username else card.render_card(
			discord_user=ctx.author, type=CardType.Kills))
		await ctx.send(file=discord.File(render.file('PNG'), 'player_card.png'))

	@rank.error
	@infamy.error
	@kills.error
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, card.UsernameError):
			await ctx.send(error.original.args[0]['message'])
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
			await webhook.send(
				f'I will leave for another mine in around {f"{hours} hours" if hours > 1 else "1 hour" if hours == 1 else ""}{" and " if hours > 0 and minutes > 0 else ""}{f"{minutes} minutes" if minutes > 0 else ""}. ')

	@peddler.error
	async def on_command_error(self, ctx, error):
		await self.handle_command_error(ctx, error)

	@commands.group()
	async def leaderboard(self, ctx):
		"""Displays the current leaderboard!"""
		if ctx.invoked_subcommand is None:
			await ctx.send(f'usage: {self.bot.command_prefix}{ctx.invoked_with} <rank|blocks|infamy|kda|kills|deaths>')

	@leaderboard.command(name='rank')
	async def leaderboard_rank(self, ctx):
		"""Displays the current leaderboard in terms of prison ranks"""
		async with ctx.typing():
			render = await card.render_leaderboard(card.LeaderboardType.Rank)
		await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

	@leaderboard.command(name='blocks')
	async def leaderboard_blocks(self, ctx):
		"""Displays the current leaderboard in terms of blocks mined"""
		async with ctx.typing():
			render = await card.render_leaderboard(card.LeaderboardType.Blocks)
		await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

	@leaderboard.command(name='infamy')
	async def leaderboard_infamy(self, ctx):
		"""Displays the current leaderboard in terms of arena Infamy"""
		async with ctx.typing():
			render = await card.render_leaderboard(card.LeaderboardType.Infamy)
		await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

	@leaderboard.command(name='kda')
	async def leaderboard_kda(self, ctx):
		"""Displays the current leaderboard in terms of arena KDA"""
		async with ctx.typing():
			render = await card.render_leaderboard(card.LeaderboardType.Kda)
		await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

	@leaderboard.command(name='kills')
	async def leaderboard_kills(self, ctx):
		"""Displays the current leaderboard in terms of arena kills"""
		async with ctx.typing():
			render = await card.render_leaderboard(card.LeaderboardType.Kills)
		await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

	@leaderboard.command(name='deaths')
	async def leaderboard_deaths(self, ctx):
		"""Displays the current leaderboard in terms of arena deaths"""
		async with ctx.typing():
			render = await card.render_leaderboard(card.LeaderboardType.Deaths)
		await ctx.send(file=discord.File(render.file('PNG'), 'leaderboard.png'))

	@leaderboard.error
	@leaderboard_rank.error
	@leaderboard_kda.error
	@leaderboard_kills.error
	@leaderboard_deaths.error
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, card.NotEnoughDataError):
			await ctx.send(f'There isn’t enough data to display the leaderboard at the moment. Please try again later!')
		else:
			await self.handle_command_error(ctx, error)

	async def handle_command_error(self, ctx, error):
		await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
		raise
