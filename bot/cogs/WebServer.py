import asyncio
import json
import os

import nextcord
from aiohttp import web
from aiohttp_apispec import docs, querystring_schema, request_schema, response_schema, setup_aiohttp_apispec
from aiohttp_remotes import BasicAuth, Secure, XForwardedRelaxed, setup
from nextcord.ext import commands, tasks

from bot.api.StreetRunnerApi.Player import Player
from bot.cosmetics import pets, titles
from docs.schema import ChannelSchema, MessageQuerySchema, MessageSchema, MessageUpdateResponseSchema, MessageUpdateSchema, UserSchema


class WebServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web_server.start()

        self.app = web.Application()

        if os.environ.get('DEV', False) == 'DEV':
            asyncio.run(setup(self.app))
        else:
            asyncio.run(setup(self.app, XForwardedRelaxed(), Secure(),
                              BasicAuth(os.environ['BASIC_USER'], os.environ['BASIC_PASS'], 'realm')))

        self.routes = web.RouteTableDef()

        @self.routes.get('/')
        async def index(request):
            return web.FileResponse('docs/index.html')

        @self.routes.get('/health')
        async def health(request):
            return web.Response()

        @docs(
            tags=['channel'],
            summary='Get channels',
            description='Retrieves a list of Discord text channels',
        )
        @response_schema(ChannelSchema(many=True), 200)
        @self.routes.get('/channels', allow_head=False)
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
                        'category': channel.category.name if channel.category else None,
                    })

            return web.json_response(response)

        @docs(
            tags=['channel'],
            summary='Send a message',
            description='Sends a message to the specified Discord channel',
            responses={
                200: {'description': 'OK'},
                400: {'description': 'Request is malformed'},
                404: {'description': 'Channel was not found'},
            },
        )
        @request_schema(MessageUpdateSchema)
        @response_schema(MessageUpdateResponseSchema)
        @self.routes.post('/channel/{id}/send')
        async def send_channel(request):
            channel = self.bot.get_channel(int(request.match_info['id']))
            if not channel:
                raise web.HTTPNotFound()

            try:
                data = await request.json()
            except json.decoder.JSONDecodeError:
                raise web.HTTPBadRequest()

            message = await self.update_message(channel.send, data)
            return web.json_response({
                'id': message.id,
            })

        @docs(
            tags=['user'],
            summary='Get user information',
            description='Retrieves information of a user',
        )
        @response_schema(UserSchema(), 200)
        @self.routes.get('/user/{id}', allow_head=False)
        async def info_user(request):
            user = self.bot.get_user(int(request.match_info['id']))
            if not user:
                raise web.HTTPNotFound()
            return web.json_response({
                'id': user.id,
                'username': user.name,
                'discriminator': user.discriminator,
                'nickname': user.display_name,
                'avatar': str(user.avatar_url),
            })

        @docs(
            tags=['user'],
            summary='Send a message',
            description='Sends a message to the specified user',
            responses={
                400: {'description': 'Request is malformed'},
                404: {'description': 'User was not found'},
            },
        )
        @request_schema(MessageUpdateSchema)
        @response_schema(MessageUpdateResponseSchema, 200)
        @self.routes.post('/user/{id}/send')
        async def send_user(request):
            user = self.bot.get_user(int(request.match_info['id']))
            if not user:
                raise web.HTTPNotFound()

            try:
                data = await request.json()
            except json.decoder.JSONDecodeError:
                raise web.HTTPBadRequest()

            message = await self.update_message(user.send, data)
            return web.json_response({
                'id': message.id,
            })

        @docs(
            tags=['user'],
            summary='Get user information',
            description='Retrieves information of a user',
        )
        @response_schema(UserSchema(), 200)
        @self.routes.get('/user/{name}/{discrim}', allow_head=False)
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
                'avatar': str(member.avatar_url),
            })

        @docs(
            tags=['user'],
            summary='Send a message',
            description='Sends a message to the specified user',
            responses={
                400: {'description': 'Request is malformed'},
                404: {'description': 'User was not found'},
            },
        )
        @request_schema(MessageUpdateSchema)
        @response_schema(MessageUpdateResponseSchema, 200)
        @self.routes.post('/user/{name}/{discrim}/send')
        async def send_member(request):
            guild = self.bot.get_guild(int(os.environ['GUILD_ID']))
            if not guild:
                raise web.HTTPNotFound()
            member = guild.get_member_named(request.match_info['name'] + '#' + request.match_info['discrim'])
            if not member:
                raise web.HTTPNotFound()

            try:
                data = await request.json()
            except json.decoder.JSONDecodeError:
                raise web.HTTPBadRequest()

            message = await self.update_message(member.send, data)
            return web.json_response({
                'id': message.id,
            })

        @docs(
            tags=['message'],
            summary='Get message information',
            description='Retrieves information about a message',
        )
        @querystring_schema(MessageQuerySchema)
        @response_schema(MessageSchema(), 200)
        @self.routes.get('/message/{channel_id}/{message_id}', allow_head=False)
        async def info_message(request):
            channel = self.bot.get_channel(int(request.match_info['channel_id']))
            if not channel:
                raise web.HTTPNotFound()

            try:
                message = await channel.fetch_message(int(request.match_info['message_id']))
            except nextcord.NotFound:
                raise web.HTTPNotFound()
            except Exception:
                raise web.HTTPInternalServerError()

            response = {
                'author': message.author.id,
                'content': message.content,
            }

            if 'embeds' in request.query:
                response['embeds'] = [embed.to_dict() for embed in message.embeds]

            if 'reactions' in request.query:
                response['reactions'] = []
                for reaction in message.reactions:
                    response['reactions'].append({
                        'reaction': reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name,
                        'users': [user.id async for user in reaction.users()],
                    })

            return web.json_response(response)

        @docs(
            tags=['message'],
            summary='Edit a message',
            description='Edits the specified message',
            responses={
                200: {'description': 'OK'},
                400: {'description': 'Request is malformed'},
                404: {'description': 'Channel or message was not found'},
            },
        )
        @request_schema(MessageUpdateSchema)
        @self.routes.post('/message/{channel_id}/{message_id}')
        async def edit_message(request):
            channel = self.bot.get_channel(int(request.match_info['channel_id']))
            if not channel:
                raise web.HTTPNotFound()

            try:
                message = await channel.fetch_message(int(request.match_info['message_id']))
            except nextcord.NotFound:
                raise web.HTTPNotFound()
            except Exception:
                raise web.HTTPInternalServerError()

            try:
                data = await request.json()
            except json.decoder.JSONDecodeError:
                raise web.HTTPBadRequest()

            await self.update_message(message.edit, data)
            return web.Response()

        @docs(
            tags=['message'],
            summary='Delete a message',
            description='Deletes the specified message',
            responses={
                200: {'description': 'OK'},
                404: {'description': 'Channel or message was not found'},
            },
        )
        @self.routes.delete('/message/{channel_id}/{message_id}')
        async def delete_message(request):
            channel = self.bot.get_channel(int(request.match_info['channel_id']))
            if not channel:
                raise web.HTTPNotFound()

            try:
                message = await channel.fetch_message(int(request.match_info['message_id']))
            except nextcord.NotFound:
                raise web.HTTPNotFound()
            except Exception:
                raise web.HTTPInternalServerError()

            await message.delete()
            return web.Response()

        @docs(
            tags=['cosmetics'],
            summary='Updates cosmetics information',
            description='Updates comsmetics information for a user',
            responses={
                200: {'description': 'OK'},
                404: {'description': 'User was not found'},
            },
        )
        @self.routes.post('/cosmetics/{uuid}')
        async def update_cosmetics(request):
            if (discord_id := (await Player({'uuid': request.match_info['uuid']}).PlayerInfo().data).discord) is None:
                raise web.HTTPOk()

            guild = self.bot.get_guild(int(os.environ['GUILD_ID']))
            if not guild:
                raise web.HTTPNotFound()

            member = guild.get_member(discord_id)
            if not member:
                raise web.HTTPNotFound()

            cosmetic_data = await request.json()

            for cosmetic_type in {*cosmetic_data.get('old', {}).keys(), *cosmetic_data.get('new', {}).keys()}:
                if cosmetic_type == 'TITLE':
                    cosmetic_from_known_string = titles.from_known_string
                    kls = titles.Title
                elif cosmetic_type == 'PET':
                    cosmetic_from_known_string = pets.from_known_string
                    kls = pets.Pet
                else:
                    continue

                cosmetic_name_new = cosmetic_data.get('new', {}).get(cosmetic_type)
                if cosmetic_name := cosmetic_data.get('old', {}).get(cosmetic_type):
                    if cosmetic_name != cosmetic_name_new:
                        if role := getattr(cosmetic_from_known_string(cosmetic_name), 'role', None):
                            await member.remove_roles(guild.get_role(role))
                else:
                    await member.remove_roles(*(guild.get_role(x) for x in kls.roles()))

                if cosmetic_name_new and cosmetic_name_new != cosmetic_name:
                    if role := getattr(cosmetic_from_known_string(cosmetic_name_new), 'role', None):
                        await member.add_roles(guild.get_role(role))

            return web.Response()

        self.webserver_port = os.environ.get('PORT', 5000)
        self.app.add_routes(self.routes)

        setup_aiohttp_apispec(
            app=self.app,
            title='StreetRunner Bot API',
            info={'description': 'A simple REST API to interface with StreetRunner Bot'},
            securityDefinitions={
                'BasicAuth': {'type': 'basic', 'name': 'Authorization', 'in': 'header'},
            },
            version='v1.4.0',
            url='/swagger.json',
        )

    async def update_message(self, f, data):
        content = data.get('content')
        embeds = [nextcord.Embed.from_dict(embed) for embed in data.get('embeds', [])]

        if not content and not embeds:
            raise web.HTTPBadRequest()

        return await f(content=content, embeds=embeds)

    @tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        await web.TCPSite(runner, host='0.0.0.0', port=self.webserver_port).start()  # noqa: S104

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()
