import discord
from discord.ext import commands
from bot import card
import os
import datetime

PEDDLER_NAME = 'Luthor'
PEDDLER_AVATAR = 'images/peddler_avatar.png'


class PlayerCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=['kda'])
	async def rank(self, ctx, username: str):
		image = await card.gen_card(username)
		await ctx.send(file=discord.File(image, 'rank_card.png'))

	@rank.error
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f'usage: {self.bot.command_prefix}rank <Minecraft username>')
		else:
			await self.handle_command_error(ctx, error)

	@commands.command(aliases=['luthor'])
	async def peddler(self, ctx):
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
		await ctx.send('Sorry, an error has occured. An admin will be notified. ')
		admin_user = self.bot.get_user(int(os.environ['ADMIN_USER_ID']))
		if admin_user:
			await admin_user.send(f'An error has occurred: {error}\nMessage: {ctx.message}')