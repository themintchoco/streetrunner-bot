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

from bot.cosmetics import titles
from bot.cosmetics.cosmetics import Cosmetics
from bot.cosmetics.pets import Pet
from bot.exceptions import *
from bot.player.leaderboard import LeaderboardType
from bot.player.stats import PlayerStatsType, PlayerStatsPrison, PlayerStatsArena, PlayerInfo
from store.RedisClient import RedisClient


@cached(cache=TTLCache(maxsize=1024, ttl=86400))
async def get_skin(uuid: str) -> dict:
    conn = RedisClient().conn
    if cached := conn.hgetall(f'skins:{uuid}'):
        return {
            'skin': BytesIO(base64.b64decode(cached[b'skin'])),
            'slim': cached[b'slim'] == b'1'
        }

    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://sessionserver.mojang.com/session/minecraft/profile/{urllib.parse.quote(uuid)}') as r:
            if r.status != 200:
                raise APIError(r)
            for prop in (await r.json())['properties']:
                if prop['name'] == 'textures':
                    skin_data = json.loads(base64.b64decode(prop['value']))['textures']['SKIN']
                    async with s.get(skin_data['url']) as r:
                        if r.status != 200:
                            raise APIError(r)
                        skin = await r.read()

                    conn.hset(f'skins:{uuid}', mapping={
                        'skin': base64.b64encode(skin).decode(),
                        'slim': 1 if skin_data.get('metadata', {}).get('model', '') == 'slim' else 0
                    })

                    conn.expire(f'skins:{uuid}', datetime.timedelta(days=1))

                    return {
                        'skin': BytesIO(skin),
                        'slim': skin_data.get('metadata', {}).get('model', '') == 'slim'
                    }
            raise


async def get_player_info(*, username: str = None, discord_user: discord.User = None,
                          type: PlayerStatsType = None) -> PlayerInfo:
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://streetrunner.dev/api/player/?{("mc_username=" + urllib.parse.quote(username)) if username else ("discord_id=" + urllib.parse.quote(str(discord_user.id)))}{f"&type={type.name.lower()}" if type else ""}',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status == 404:
                if username:
                    raise UsernameError({'message': f'The username provided is invalid', 'username': username})
                else:
                    raise DiscordNotLinkedError({
                        'message': f'You have not linked your Discord account to your Minecraft account. Please link your account using the /discord command in-game. ',
                        'discord_id': discord_user})
            elif r.status != 200:
                raise APIError(r)

            player_data = await r.json()

    player_stats_prison = None
    player_stats_arena = None
    player_time_played = None

    if prison_data := player_data.get('prison', None):
        player_stats_prison = PlayerStatsPrison(rank=prison_data['rank'], blocks=prison_data['amount'])

    if arena_data := player_data.get('arena', None):
        player_stats_arena = PlayerStatsArena(infamy=arena_data['infamy'], kills=arena_data['kills'],
                                              deaths=arena_data['deaths'], assists=arena_data['assists'])

    if time_played := player_data.get('time', None):
        player_time_played = datetime.timedelta(seconds=time_played)

    return PlayerInfo(player_data['uuid'], player_data['username'], stats_prison=player_stats_prison,
                      stats_arena=player_stats_arena, time_played=player_time_played)


async def get_player_cosmetics(*, username: str = None, discord_user: discord.User = None) -> List[Cosmetics]:
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://streetrunner.dev/api/cosmetic/?{("mc_username=" + urllib.parse.quote(username)) if username else ("discord_id=" + urllib.parse.quote(str(discord_user.id)))}',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status == 404:
                if username:
                    raise UsernameError({'message': f'The username provided is invalid', 'username': username})
                else:
                    raise DiscordNotLinkedError({
                        'message': f'You have not linked your Discord account to your Minecraft account. Please link your account using the /discord command in-game. ',
                        'discord_id': discord_user})
            elif r.status != 200:
                raise APIError(r)

            cosmetics_data = await r.json()

    cosmetics = []

    if title := cosmetics_data.get('TITLE', None):
        cosmetics.append(titles.from_known_string(title))

    if pet := cosmetics_data.get('PET', None):
        cosmetics.append(Pet(pet_type=pet))

    return cosmetics


async def get_leaderboard(type: LeaderboardType) -> AsyncGenerator[PlayerInfo, None]:
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://streetrunner.dev/api/leaderboard/?type={type.name.lower()}',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status != 200:
                raise APIError(r)
            leaderboard_data = await r.json()

    for player_data in leaderboard_data[type.name.lower()]:
        player_stats_prison = None
        player_stats_arena = None
        player_time_played = None

        if prison_data := player_data.get('prison', None):
            player_stats_prison = PlayerStatsPrison(rank=prison_data['rank'], blocks=prison_data['amount'])

        if arena_data := player_data.get('arena', None):
            player_stats_arena = PlayerStatsArena(infamy=arena_data['infamy'], kills=arena_data['kills'],
                                                  deaths=arena_data['deaths'], assists=arena_data['assists'])

        if time_played := player_data.get('time', None):
            player_time_played = datetime.timedelta(seconds=time_played)

        yield PlayerInfo(player_data['uuid'], player_data['username'], stats_prison=player_stats_prison,
                         stats_arena=player_stats_arena, time_played=player_time_played)


async def get_position(*, username: str = None, discord_user: discord.User = None, type: LeaderboardType) -> int:
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://streetrunner.dev/api/position/?{("mc_username=" + urllib.parse.quote(username)) if username else ("discord_id=" + urllib.parse.quote(str(discord_user.id)))}&type={type.name.lower()}',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status == 404:
                raise UsernameError({'message': f'The username provided is invalid',
                                     'username': username}) if username else DiscordNotLinkedError()
            elif r.status != 200:
                raise APIError(r)
            return (await r.json())[type.name.lower()]

async def get_chat_xp(discord_id: List[int], timerange: List[Tuple[datetime.datetime, datetime.datetime]]) -> List[int]:
    query = {'data': [{
        'discord_id': str(discord_id[i]),
        'start': int(timerange[i][0].timestamp()),
        'end': int(timerange[i][1].timestamp())
    } for i in range(len(discord_id))],
        'cooldown': 8}

    async with aiohttp.ClientSession() as s:
        async with s.post(
                f'https://streetrunner.dev/api/chat/', json=query,
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status != 200:
                raise APIError(r)

            return await r.json()
