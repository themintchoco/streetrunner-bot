import json
import os

from aiohttp import web
from aiohttp_basicauth import BasicAuthMiddleware
from discord.ext import commands, tasks


class WebServer(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.web_server.start()

		auth = BasicAuthMiddleware(
			username=os.environ['BASIC_USER'],
			password=os.environ['BASIC_PASS'],
			force=False
		)

		self.app = web.Application(middlewares=[auth])
		self.routes = web.RouteTableDef()

		@self.routes.get('/')
		async def index(request):
			raise web.HTTPFound('https://streetrunner.dev')

		@self.routes.get('/channels')
		@auth.required
		async def list_channels(request):
			guild = self.bot.get_guild(int(os.environ['GUILD_ID']))
			if not guild:
				raise web.HTTPNotFound()

			response = []
			for channel in guild.channels:
				if str(channel.type) == 'text':
					response.append({
						'id': channel.id,
						'name': channel.name,
						'category': channel.category.name if channel.category else None
					})

			return web.json_response(response)

		@self.routes.post('/channel/{id}/send')
		@auth.required
		async def send_channel(request):
			channel = self.bot.get_channel(int(request.match_info['id']))
			if not channel:
				raise web.HTTPNotFound()

			msg = await request.text()
			try:
				await channel.send(embed=discord.Embed.from_dict(json.loads(msg)))
			except json.decoder.JSONDecodeError:
				await channel.send(msg)

			return web.Response()

		@self.routes.get('/user/{id}')
		@auth.required
		async def info_user(request):
			user = self.bot.get_user(int(request.match_info['id']))
			if not user:
				raise web.HTTPNotFound()
			return web.json_response({
				'id': user.id,
				'username': user.name,
				'discriminator': user.discriminator,
				'nickname': user.display_name,
				'avatar': str(user.avatar_url)
			})

		@self.routes.post('/user/{id}/send')
		@auth.required
		async def send_user(request):
			user = self.bot.get_user(int(request.match_info['id']))
			if not user:
				raise web.HTTPNotFound()

			msg = await request.text()
			try:
				await user.send(embed=discord.Embed.from_dict(json.loads(msg)))
			except json.decoder.JSONDecodeError:
				await user.send(msg)

			return web.Response()

		@self.routes.get('/user/{name}/{discrim}')
		@auth.required
		async def info_member(request):
			guild = self.bot.get_guild(int(os.environ['GUILD_ID']))
			if not guild:
				raise web.HTTPNotFound()
			member = guild.get_member_named(request.match_info['name'] + '#' + request.match_info['discrim'])
			if not member:
				raise web.HTTPNotFound()
			return web.json_response({
				'id': member.id,
				'username': member.name,
				'discriminator': member.discriminator,
				'nickname': member.display_name,
				'avatar': str(member.avatar_url)
			})

		@self.routes.post('/user/{name}/{discrim}/send')
		@auth.required
		async def send_member(request):
			guild = self.bot.get_guild(int(os.environ['GUILD_ID']))
			if not guild:
				raise web.HTTPNotFound()
			member = guild.get_member_named(request.match_info['name'] + '#' + request.match_info['discrim'])
			if not member:
				raise web.HTTPNotFound()

			msg = await request.text()
			try:
				await member.send(embed=discord.Embed.from_dict(json.loads(msg)))
			except json.decoder.JSONDecodeError:
				await member.send(msg)

			return web.Response()

		self.webserver_port = os.environ.get('PORT', 5000)
		self.app.add_routes(self.routes)

	@tasks.loop()
	async def web_server(self):
		runner = web.AppRunner(self.app)
		await runner.setup()
		await web.TCPSite(runner, host='0.0.0.0', port=self.webserver_port).start()

	@web_server.before_loop
	async def web_server_before_loop(self):
		await self.bot.wait_until_ready()
