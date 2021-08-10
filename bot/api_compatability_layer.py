import base64
import datetime
import json
import os
import urllib
from io import BytesIO
from typing import AsyncGenerator, List, Tuple

import aiohttp
import discord
from asyncache import cached
from cachetools import TTLCache

from api.SkinsApi.SkinsApi import SkinsApi
from api.StreetRunnerApi.Player import Player
from api.StreetRunnerApi.Leaderboard import Leaderboard
from bot.cosmetics import titles
from bot.cosmetics.cosmetics import Cosmetics
from bot.cosmetics.pets import Pet
from bot.exceptions import APIError, DiscordNotLinkedError, UsernameError
from bot.player.leaderboard import LeaderboardType
from bot.player.stats import PlayerInfo, PlayerStatsArena, PlayerStatsPrison, PlayerStatsType
from store.RedisClient import RedisClient


@cached(cache=TTLCache(maxsize=1024, ttl=86400))
async def get_skin(uuid: str) -> dict:
    conn = RedisClient().conn
    if cached := conn.hgetall(f'skins:{uuid}'):
        return {
            'skin': BytesIO(base64.b64decode(cached[b'skin'])),
            'slim': cached[b'slim'] == b'1',
        }

    skin_data = await SkinsApi({'uuid': uuid}).adata

    for prop in skin_data.properties:
        if prop['name'] == 'textures':
            async with aiohttp.ClientSession() as s:
                async with s.get(json.loads(base64.b64decode(prop['value']))['textures']['SKIN']['url']) as r:
                    if r.status != 200:
                        raise APIError(r)
                    skin = await r.read()

            conn.hset(f'skins:{uuid}', mapping={
                'skin': base64.b64encode(skin).decode(),
                'slim': 1 if skin_data.get('metadata', {}).get('model', '') == 'slim' else 0,
            })

            conn.expire(f'skins:{uuid}', datetime.timedelta(days=1))

            return {
                'skin': BytesIO(skin),
                'slim': skin_data.get('metadata', {}).get('model', '') == 'slim',
            }

    raise ApiError()


async def get_player_info(*, username: str = None, discord_user: discord.User = None,
                          type: PlayerStatsType = None) -> PlayerInfo:
    try:
        player = Player({'mc_username': username, 'discord_id': discord_user.id})

    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            if username:
                raise UsernameError({'message': 'The username provided is invalid', 'username': username})
            else:
                raise DiscordNotLinkedError({
                    'message': 'You have not linked your Discord account to your Minecraft account. '
                               'Please link your account using the /discord command in-game. ',
                    'discord_id': discord_user})

        raise APIError(r)

    return PlayerInfo(player)


async def get_player_cosmetics(*, username: str = None, discord_user: discord.User = None) -> List[Cosmetics]:
    try:
        cosmetics_data = await Player({'mc_username': username, 'discord_id': discord_user.id}).PlayerCosmetics().adata

    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            if username:
                raise UsernameError({'message': 'The username provided is invalid', 'username': username})
            else:
                raise DiscordNotLinkedError({
                    'message': 'You have not linked your Discord account to your Minecraft account. '
                               'Please link your account using the /discord command in-game. ',
                    'discord_id': discord_user})

    cosmetics = []

    if title := cosmetics_data.get('TITLE', None):
        cosmetics.append(titles.from_known_string(title))

    if pet := cosmetics_data.get('PET', None):
        cosmetics.append(Pet(pet_type=pet))

    return cosmetics


async def get_leaderboard(leaderboard_type) -> AsyncGenerator[PlayerInfo, None]:
    try:
        leaderboard_data = await leaderboard_type().adata

    except aiohttp.ClientResponseError as e:
        raise APIError(r)

    for entry in leaderboard_data:
        yield PlayerInfo(Player({'uuid': entry.uuid}))


async def get_position(*, username: str = None, discord_user: discord.User = None, leaderboard_type) -> int:
    try:
        position = (await leaderboard_type().LeaderboardDataPosition().adata).value

    except aiohttp.ClientResponseError as e:
        raise APIError(r)

    return position


async def get_chat_xp(discord_id: List[int], timerange: List[Tuple[datetime.datetime, datetime.datetime]]) -> List[int]:
    query = {'data': [{
        'discord_id': str(discord_id[i]),
        'start': int(timerange[i][0].timestamp()),
        'end': int(timerange[i][1].timestamp()),
    } for i in range(len(discord_id))],
        'cooldown': 8}

    async with aiohttp.ClientSession() as s:
        async with s.post(
                'https://streetrunner.dev/api/chat/', json=query,
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status != 200:
                raise APIError(r)

            return await r.json()
