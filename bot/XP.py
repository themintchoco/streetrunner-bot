import asyncio
import datetime
import os
import urllib.parse

import aiohttp
from discord.ext import commands
from sqlalchemy import select

from bot.exceptions import DiscordNotLinkedError
from store.PostgresClient import PostgresClient
from store.User import User


class XP(commands.Cog):
	xp_cooldown = {}

	def __init__(self, bot):
		self.bot = bot

	@classmethod
	async def process_message(cls, message):
		if message.author.id in cls.xp_cooldown:
			return

		cls.xp_cooldown[message.author.id] = True

		with PostgresClient().session() as session:
			user = session.execute(
				select(User)
					.where(User.discord_id == message.author.id)
			).scalar()

			if not user:
				user = User(discord_id=message.author.id,
							xp=0,
							xp_refreshed=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
				session.add(user)

			user.xp += 1
			session.commit()

		await asyncio.sleep(8)
		cls.xp_cooldown.pop(message.author.id, None)

	@commands.command(hidden=True)
	async def xp(self, ctx):
		with PostgresClient().session() as session:
			user = session.execute(
				select(User)
					.where(User.discord_id == ctx.author.id)
			).scalar()

			if not user:
				user = User(discord_id=ctx.author.id,
							xp=0,
							xp_refreshed=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
				session.add(user)

			refresh_time = datetime.datetime.now(datetime.timezone.utc).timestamp()

			query = {'start': int(user.xp_refreshed.timestamp()),
					 'end': int(refresh_time),
					 'cooldown': 8,
					 'discord_id': ctx.author.id}

			async with aiohttp.ClientSession() as s:
				try:
					async with s.get(
							f'https://streetrunner.dev/api/chat?{urllib.parse.urlencode(query)}',
							headers={'Authorization': os.environ['API_KEY']}) as r:
						if r.status == 404:
							raise DiscordNotLinkedError()
						elif r.status != 200:
							raise

						xp_delta = int(await r.text())
						user.xp += xp_delta
						user.xp_refreshed = refresh_time
						session.commit()

				except DiscordNotLinkedError:
					pass

		await ctx.send(f'xp: {user.xp}')

	@xp.error
	async def on_command_error(self, ctx, error):
		await self.handle_command_error(ctx, error)

	async def handle_command_error(self, ctx, error):
		await ctx.send('Sorry, an error has occured. Please try again at a later time. ')
		raise