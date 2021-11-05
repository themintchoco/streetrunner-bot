import base64
import datetime
import json
import os
from io import BytesIO
from typing import AsyncGenerator, List, Tuple

import aiohttp
import discord
from asyncache import cached
from cachetools import TTLCache

from bot.api.SkinsApi.SkinsApi import SkinsApi
from bot.api.StreetRunnerApi.Player import Player
from bot.cosmetics import titles
from bot.cosmetics.cosmetics import Cosmetics
from bot.cosmetics.pets import Pet
from bot.exceptions import APIError, DiscordNotLinkedError, UsernameError
from bot.player.stats import PlayerInfo
from store.RedisClient import RedisClient


@cached(cache=TTLCache(maxsize=1024, ttl=86400))
async def get_skin(uuid: str) -> dict:
    conn = RedisClient().conn
    if cached := await conn.hgetall(f'skins:{uuid}'):
        return {
            'skin': BytesIO(base64.b64decode(cached[b'skin'])),
            'slim': cached[b'slim'] == b'1',
        }

    skin_data = await SkinsApi({'uuid': uuid}).data

    for prop in skin_data.properties:
        if prop['name'] == 'textures':
            async with aiohttp.ClientSession() as s:
                async with s.get(json.loads(base64.b64decode(prop['value']))['textures']['SKIN']['url']) as r:
                    if r.status != 200:
                        raise APIError(r)
                    skin = await r.read()

            await conn.hset(f'skins:{uuid}', mapping={
                'skin': base64.b64encode(skin).decode(),
                'slim': 1 if skin_data.get('metadata', {}).get('model', '') == 'slim' else 0,
            })

            await conn.expire(f'skins:{uuid}', datetime.timedelta(days=1))

            return {
                'skin': BytesIO(skin),
                'slim': skin_data.get('metadata', {}).get('model', '') == 'slim',
            }

    raise APIError()


@cached(cache=TTLCache(maxsize=1024, ttl=86400))
async def resolve_uuid(*, username: str = None, discord_id: int = None) -> str:
    conn = RedisClient().conn
    cache_key = f'uuid:username:{username}' if username else f'uuid:discord:{discord_id}'

    if cached := await conn.get(cache_key):
        return cached.decode()

    try:
        uuid = (await Player({'mc_username': username, 'discord_id': discord_id}).PlayerInfo().data).uuid
        await conn.set(cache_key, uuid, ex=datetime.timedelta(days=1))
        return uuid

    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            if username:
                raise UsernameError({'message': 'The username provided is invalid', 'username': username})
            else:
                raise DiscordNotLinkedError({
                    'message': f'<@{discord_id}> is not linked to StreetRunner. '
                               'Linking can be done by using the /discord command in-game. ',
                    'discord_id': discord_id})
        raise APIError(e)


async def get_player_info(*, username: str = None, discord_user: discord.User = None, type=None) -> PlayerInfo:
    try:
        player = Player({
            'mc_username': username if username else None,
            'discord_id': discord_user.id if discord_user else None,
        })

    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            if username:
                raise UsernameError({'message': 'The username provided is invalid', 'username': username})
            else:
                raise DiscordNotLinkedError({
                    'message': f'<@{discord_user.id}> is not linked to StreetRunner. '
                               'Linking can be done by using the /discord command in-game. ',
                    'discord_id': discord_user.id})

        raise APIError(e)

    return PlayerInfo(player)


async def get_player_cosmetics(*, username: str = None, discord_user: discord.User = None) -> List[Cosmetics]:
    try:
        cosmetics_data = await Player({
            'mc_username': username if username else None,
            'discord_id': discord_user.id if discord_user else None,
        }).PlayerCosmetics().data

    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            if username:
                raise UsernameError({'message': 'The username provided is invalid', 'username': username})
            else:
                raise DiscordNotLinkedError({
                    'message': f'<@{discord_user.id}> is not linked to StreetRunner. '
                               'Linking can be done by using the /discord command in-game. ',
                    'discord_id': discord_user})
        raise APIError(e)

    cosmetics = []

    for cosmetic_data in cosmetics_data:
        if cosmetic_data.type == 'TITLE':
            cosmetics.append(titles.from_known_string(cosmetic_data.name))

        if cosmetic_data.type == 'PET':
            cosmetics.append(Pet(pet_type=cosmetic_data.name))

    return cosmetics


async def get_leaderboard(leaderboard_type) -> AsyncGenerator[PlayerInfo, None]:
    try:
        leaderboard_data = await leaderboard_type().data

    except aiohttp.ClientResponseError as e:
        raise APIError(e)

    for entry in leaderboard_data:
        yield PlayerInfo(Player({'uuid': entry.uuid}))


async def get_position(*, username: str = None, discord_user: discord.User = None, leaderboard_type) -> int:
    try:
        position = (await leaderboard_type().LeaderboardDataPosition({
            'uuid': await resolve_uuid(username=username, discord_id=discord_user.id if discord_user else None),
        }).data).value

    except aiohttp.ClientResponseError as e:
        raise APIError(e)

    return position


async def get_chat_xp(discord_id: List[int], timerange: List[Tuple[datetime.datetime, datetime.datetime]]) -> List[int]:
    query = []
    id_map = {}

    for i in range(len(discord_id)):
        query.append({
            'id': str(discord_id[i]),
            'start': int(timerange[i][0].timestamp()),
            'end': int(timerange[i][1].timestamp()),
            'cooldown': 8,
        })

        id_map[str(discord_id[i])] = i

    async with aiohttp.ClientSession() as s:
        async with s.post(
                'https://streetrunner.gg/api/xp/', json=query,
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status != 200:
                raise APIError(r)

            result = await r.json()

    deltas = [0] * len(discord_id)

    for delta in result:
        deltas[id_map[delta['id']]] = delta['value']

    return deltas
