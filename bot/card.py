import asyncio
import base64
import datetime
import json
import os
import urllib
from enum import Enum
from io import BytesIO
from typing import AsyncGenerator, List, Tuple

import aiohttp
import asyncstdlib as a
import discord
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from asyncache import cached
from cachetools import TTLCache
from sqlalchemy import select

import bot.utilities
from bot.exceptions import UsernameError, DiscordNotLinkedError, NotEnoughDataError
from store.PostgresClient import PostgresClient
from store.RedisClient import RedisClient
from store.User import User

PLAYER_CARD_WIDTH = 640
PLAYER_CARD_HEIGHT = 220

LEADERBOARD_WIDTH = 540
LEADERBOARD_HEIGHT = 500

XP_CARD_WIDTH = 640
XP_CARD_HEIGHT = 220

XP_LEADERBOARD_WIDTH = 580

SPACING = 12

FONT_BLACK = 'fonts/Roboto-Black.ttf'
FONT_BOLD = 'fonts/Roboto-Bold.ttf'
FONT_REGULAR = 'fonts/Roboto-Regular.ttf'
FONT_LIGHT = 'fonts/Roboto-Light.ttf'


class CardType(Enum):
    Prison, Infamy, Kills = range(3)


class PlayerStatsType(Enum):
    Prison, Arena = range(2)


class LeaderboardType(Enum):
    Rank, Kda, Kills, Blocks, Infamy, Deaths = range(6)


class CosmeticsType(Enum):
    Title, Pet = range(2)


class Cosmetics:
    def __init__(self, **kwargs):
        self.type = kwargs['type']


class CosmeticsTitle(Cosmetics):
    def __init__(self, **kwargs):
        super().__init__(type=CosmeticsType.Title)
        self.string = kwargs['string']
        self.attributes = kwargs['attributes']

    @classmethod
    def from_known_string(cls, string: str):
        return cls(**{'FIERY': {'string': 'FIERY', 'attributes': {'bold': False, 'color': (252, 84, 84, 255)}},
                      'FIERY_BOLD': {'string': 'FIERY', 'attributes': {'bold': True, 'color': (252, 84, 84, 255)}},
                      'UNDEFEATED': {'string': 'UNDEFEATED', 'attributes': {'bold': True, 'color': (252, 84, 252, 255)}},
                      'SUPREME': {'string': 'SUPREME', 'attributes': {'bold': True, 'color': (252, 168, 0, 255)}},
                      'DRAKE': {'string': 'DRAKE', 'attributes': {'bold': False, 'color': (168, 0, 0, 255)}},
                      }[string])


class CosmeticsPet(Cosmetics):
    def __init__(self, **kwargs):
        super().__init__(type=CosmeticsType.Pet)
        self.pet_type = kwargs['pet_type']


class PlayerStats:
    def __init__(self, **kwargs):
        self.type = kwargs['type']


class PlayerStatsPrison(PlayerStats):
    def __init__(self, **kwargs):
        super().__init__(type=PlayerStatsType.Prison)
        self.rank = kwargs['rank']
        self.blocks = kwargs['blocks']


class PlayerStatsArena(PlayerStats):
    def __init__(self, **kwargs):
        super().__init__(type=PlayerStatsType.Arena)
        self.infamy = kwargs['infamy']
        self.kills = kwargs['kills']
        self.deaths = kwargs['deaths']
        self.assists = kwargs['assists']

    @property
    def kda(self) -> float:
        return round((self.kills + self.assists) / max(self.deaths, 1), 2)


class PlayerInfo:
    def __init__(self, uuid, username, **kwargs):
        self.uuid = uuid
        self.username = username
        self.stats_prison = kwargs.get('stats_prison', None)
        self.stats_arena = kwargs.get('stats_arena', None)


class Render:
    def __init__(self, *images: Image.Image):
        self._images = images

    @property
    def image(self) -> Image.Image:
        return self._images[0]

    @property
    def multi_frame(self) -> bool:
        return len(self._images) > 1

    def file(self, *args, **kwargs) -> BytesIO:
        fp = BytesIO()
        self.image.save(fp, *args, **kwargs)
        fp.seek(0)

        return fp

    def file_animated(self, *args, **kwargs) -> BytesIO:
        fp = BytesIO()
        self.image.save(fp, save_all=True, append_images=self._images[1:], *args, **kwargs)
        fp.seek(0)

        return fp


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
                raise
            for prop in (await r.json())['properties']:
                if prop['name'] == 'textures':
                    skin_data = json.loads(base64.b64decode(prop['value']))['textures']['SKIN']
                    async with s.get(skin_data['url']) as r:
                        if r.status != 200:
                            raise
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
                f'https://streetrunner.dev/api/player?{("mc_username=" + urllib.parse.quote(username)) if username else ("discord_id=" + urllib.parse.quote(str(discord_user.id)))}{f"&type={type.name.lower()}" if type else ""}',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status == 404:
                if username:
                    raise UsernameError({'message': f'The username provided is invalid', 'username': username})
                else:
                    raise DiscordNotLinkedError({
                        'message': f'You have not linked your Discord account to your Minecraft account. Please link your account using the /discord command in-game. ',
                        'discord_id': discord_user})
            elif r.status != 200:
                raise

            player_data = await r.json()

    player_stats_prison = None
    player_stats_arena = None

    if prison_data := player_data.get('prison', None):
        player_stats_prison = PlayerStatsPrison(rank=prison_data['rank'], blocks=prison_data['amount'])

    if arena_data := player_data.get('arena', None):
        player_stats_arena = PlayerStatsArena(infamy=arena_data['infamy'], kills=arena_data['kills'],
                                              deaths=arena_data['deaths'], assists=arena_data['assists'])

    return PlayerInfo(player_data['uuid'], player_data['username'], stats_prison=player_stats_prison,
                      stats_arena=player_stats_arena)


async def get_player_cosmetics(*, username: str = None, discord_user: discord.User = None) -> List[Cosmetics]:
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://streetrunner.dev/api/cosmetic?{("mc_username=" + urllib.parse.quote(username)) if username else ("discord_id=" + urllib.parse.quote(str(discord_user.id)))}',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status == 404:
                if username:
                    raise UsernameError({'message': f'The username provided is invalid', 'username': username})
                else:
                    raise DiscordNotLinkedError({
                        'message': f'You have not linked your Discord account to your Minecraft account. Please link your account using the /discord command in-game. ',
                        'discord_id': discord_user})
            elif r.status != 200:
                raise

            cosmetics_data = await r.json()

    cosmetics = []

    if title := cosmetics_data.get('TITLE', None):
        cosmetics.append(CosmeticsTitle.from_known_string(title))

    if pet := cosmetics_data.get('PET', None):
        cosmetics.append(CosmeticsPet(pet_type=pet))

    return cosmetics


async def get_leaderboard(type: LeaderboardType) -> AsyncGenerator[PlayerInfo, None]:
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://streetrunner.dev/api/leaderboard?type={type.name.lower()}',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status != 200:
                raise
            leaderboard_data = await r.json()

    for player_data in leaderboard_data[type.name.lower()]:
        player_stats_prison = None
        player_stats_arena = None

        if prison_data := player_data.get('prison', None):
            player_stats_prison = PlayerStatsPrison(rank=prison_data['rank'], blocks=prison_data['amount'])

        if arena_data := player_data.get('arena', None):
            player_stats_arena = PlayerStatsArena(infamy=arena_data['infamy'], kills=arena_data['kills'],
                                                  deaths=arena_data['deaths'], assists=arena_data['assists'])

        yield PlayerInfo(player_data['uuid'], player_data['username'], stats_prison=player_stats_prison,
                         stats_arena=player_stats_arena)


async def get_position(*, username: str = None, discord_user: discord.User = None, type: LeaderboardType) -> int:
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://streetrunner.dev/api/position/?{("mc_username=" + urllib.parse.quote(username)) if username else ("discord_id=" + urllib.parse.quote(str(discord_user.id)))}&type={type.name.lower()}',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status == 404:
                raise UsernameError({'message': f'The username provided is invalid',
                                     'username': username}) if username else DiscordNotLinkedError()
            elif r.status != 200:
                raise
            return (await r.json())[type.name.lower()]


def get_number_representation(number: int) -> str:
    magnitude = (len(str(number)) - 1) // 3
    return f'{(number / (10 ** (magnitude * 3))):.3g}{" KMGTPEZY"[magnitude] if magnitude > 0 else ""}'


def get_level_from_xp(xp: int) -> int:
    i = 1
    while True:
        if get_min_xp_for_level(i) > xp:
            return i - 1
        i += 1


def get_min_xp_for_level(level: int) -> int:
    if level > 0:
        return 20 * (level - 1) ** 2 + 35
    return 0


async def get_xp(discord_user: discord.User):
    async with PostgresClient().session() as session:
        user = (await session.execute(
            select(User)
                .where(User.discord_id == discord_user.id)
        )).scalar()

        if not user:
            user = User(discord_id=discord_user.id,
                        xp=0,
                        xp_refreshed=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
            session.add(user)

        refresh_time = datetime.datetime.now(datetime.timezone.utc)

        xp_delta = (await get_chat_xp([user.discord_id], [(user.xp_refreshed, refresh_time)]))[0]
        if xp_delta is not None:
            user.xp += xp_delta
            user.xp_refreshed = refresh_time
            await session.commit()

        return user.xp


async def get_all_xp():
    async with PostgresClient().session() as session:
        users = (await session.execute(select(User))).scalars().all()

        refresh_time = datetime.datetime.now(datetime.timezone.utc)
        for i, xp_delta in enumerate(await get_chat_xp([user.discord_id for user in users],
                                                       [(user.xp_refreshed, refresh_time) for user in users])):
            if xp_delta is not None:
                users[i].xp += xp_delta
                users[i].xp_refreshed = refresh_time

        await session.commit()
        return users


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
                raise

            return await r.json()


async def render_avatar(skin, scale: int) -> Render:
    image_skin = Image.open(skin)

    head_front = image_skin.crop((8, 8, 16, 16)).resize((8 * scale, 8 * scale), Image.NEAREST)
    if image_skin.crop((32, 0, 64, 32)).getextrema()[3][0] < 255:
        head_front.alpha_composite(image_skin.crop((40, 8, 48, 16)).resize((8 * scale, 8 * scale), Image.NEAREST))

    return Render(head_front)


async def render_model(skin, slim: bool, scale: int) -> Render:
    image_render = Image.new('RGBA', (20 * scale, 45 * scale), (0, 0, 0, 0))

    image_skin = Image.open(skin)
    skin_is_old = image_skin.height == 32
    arm_width = 3 if slim else 4

    head_top = image_skin.crop((8, 0, 16, 8)).resize((8 * scale, 8 * scale), Image.NEAREST)
    head_front = image_skin.crop((8, 8, 16, 16)).resize((8 * scale, 8 * scale), Image.NEAREST)
    head_right = image_skin.crop((0, 8, 8, 16)).resize((8 * scale, 8 * scale), Image.NEAREST)

    arm_right_top = image_skin.crop((44, 16, 44 + arm_width, 20)).resize((arm_width * scale, 4 * scale), Image.NEAREST)
    arm_right_front = image_skin.crop((44, 20, 44 + arm_width, 32)).resize(
        (arm_width * scale, 12 * scale), Image.NEAREST)
    arm_right_side = image_skin.crop((40, 20, 44, 32)).resize((4 * scale, 12 * scale), Image.NEAREST)

    arm_left_top = arm_right_top.transpose(method=Image.FLIP_LEFT_RIGHT) if skin_is_old else image_skin.crop(
        (36, 48, 36 + arm_width, 52)).resize((arm_width * scale, 4 * scale), Image.NEAREST)
    arm_left_front = arm_right_front.transpose(method=Image.FLIP_LEFT_RIGHT) if skin_is_old else image_skin.crop(
        (36, 52, 36 + arm_width, 64)).resize((arm_width * scale, 12 * scale), Image.NEAREST)

    leg_right_front = image_skin.crop((4, 20, 8, 32)).resize((4 * scale, 12 * scale), Image.NEAREST)
    leg_right_side = image_skin.crop((0, 20, 4, 32)).resize((4 * scale, 12 * scale), Image.NEAREST)

    leg_left_front = leg_right_front.transpose(method=Image.FLIP_LEFT_RIGHT) if skin_is_old else image_skin.crop(
        (20, 52, 24, 64)).resize((4 * scale, 12 * scale), Image.NEAREST)

    body_front = image_skin.crop((20, 20, 28, 32)).resize((8 * scale, 12 * scale), Image.NEAREST)

    if image_skin.crop((32, 0, 64, 32)).getextrema()[3][0] < 255:
        head_top.alpha_composite(image_skin.crop((40, 0, 48, 8)).resize((8 * scale, 8 * scale), Image.NEAREST))
        head_front.alpha_composite(image_skin.crop((40, 8, 48, 16)).resize((8 * scale, 8 * scale), Image.NEAREST))
        head_right.alpha_composite(image_skin.crop((32, 8, 40, 16)).resize((8 * scale, 8 * scale), Image.NEAREST))

    if not skin_is_old:
        if image_skin.crop((16, 32, 48, 48)).getextrema()[3][0] < 255:
            body_front.alpha_composite(
                image_skin.crop((20, 36, 28, 48)).resize((8 * scale, 12 * scale), Image.NEAREST))

        if image_skin.crop((48, 48, 64, 64)).getextrema()[3][0] < 255:
            arm_right_top.alpha_composite(
                image_skin.crop((44, 32, 44 + arm_width, 36)).resize((arm_width * scale, 4 * scale), Image.NEAREST))
            arm_right_front.alpha_composite(
                image_skin.crop((44, 36, 44 + arm_width, 48)).resize((arm_width * scale, 12 * scale), Image.NEAREST))
            arm_right_side.alpha_composite(
                image_skin.crop((40, 36, 44, 48)).resize((4 * scale, 12 * scale), Image.NEAREST))

        if image_skin.crop((40, 32, 56, 48)).getextrema()[3][0] < 255:
            arm_left_top.alpha_composite(
                image_skin.crop((52, 48, 52 + arm_width, 52)).resize((arm_width * scale, 4 * scale), Image.NEAREST))
            arm_left_front.alpha_composite(
                image_skin.crop((52, 52, 52 + arm_width, 64)).resize((arm_width * scale, 12 * scale), Image.NEAREST))

        if image_skin.crop((0, 32, 16, 48)).getextrema()[3][0] < 255:
            leg_right_front.alpha_composite(
                image_skin.crop((4, 36, 8, 48)).resize((4 * scale, 12 * scale), Image.NEAREST))
            leg_right_side.alpha_composite(
                image_skin.crop((0, 36, 4, 48)).resize((4 * scale, 12 * scale), Image.NEAREST))

        if image_skin.crop((0, 48, 16, 64)).getextrema()[3][0] < 255:
            leg_left_front.alpha_composite(
                image_skin.crop((4, 52, 8, 64)).resize((4 * scale, 12 * scale), Image.NEAREST))

    front = Image.new('RGBA', (16 * scale, 24 * scale), (0, 0, 0, 0))
    front.alpha_composite(arm_right_front, ((4 - arm_width) * scale, 0))
    front.alpha_composite(arm_left_front, (12 * scale, 0))
    front.alpha_composite(body_front, (4 * scale, 0))
    front.alpha_composite(leg_right_front, (4 * scale, 12 * scale))
    front.alpha_composite(leg_left_front, (8 * scale, 12 * scale))

    x_offset = 2 * scale
    z_offset = 3 * scale

    x = x_offset + scale * 2
    y = scale * -arm_width
    z = z_offset + scale * 8
    render_top = Image.new('RGBA', (image_render.width * 4, image_render.height * 4), (0, 0, 0, 0))
    render_top.paste(arm_right_top, (
        y - z + (render_top.width - image_render.width) // 2,
        x + z + (render_top.height - image_render.height) // 2))

    y = scale * 8
    render_top.alpha_composite(arm_left_top, (
        y - z + (render_top.width - image_render.width) // 2,
        x + z + (render_top.height - image_render.height) // 2))

    x = x_offset
    y = 0
    z = z_offset
    render_top.alpha_composite(head_top, (
        y - z + (render_top.width - image_render.width) // 2,
        x + z + (render_top.height - image_render.height) // 2))

    render_top = render_top.transform((render_top.width * 2, render_top.height), Image.AFFINE,
                                      (0.5, -45 / 52, 0, 0.5, 45 / 52, 0))

    x = x_offset + scale * 2
    y = 0
    z = z_offset + scale * 20
    render_right = Image.new('RGBA', (image_render.width, image_render.height), (0, 0, 0, 0))
    render_right.paste(leg_right_side, (x + y, z - y))

    x = x_offset + scale * 2
    y = scale * -arm_width
    z = z_offset + scale * 8
    render_right.alpha_composite(arm_right_side, (x + y, z - y))

    x = x_offset
    y = 0
    z = z_offset
    render_right_head = Image.new('RGBA', (image_render.width, image_render.height), (0, 0, 0, 0))
    render_right_head.alpha_composite(head_right, (x + y, z - y))

    render_right = render_right.transform((image_render.width, image_render.height), Image.AFFINE,
                                          (1, 0, 0, -0.5, 45 / 52, 0))
    render_right_head = render_right_head.transform((image_render.width, image_render.height), Image.AFFINE,
                                                    (1, 0, 0, -0.5, 45 / 52, 0))

    x = x_offset + scale * 2
    y = 0
    z = z_offset + scale * 12
    render_front = Image.new('RGBA', (image_render.width, image_render.height), (0, 0, 0, 0))
    render_front.paste(front, (y + x, x + z))

    x = x_offset + 8 * scale
    y = 0
    z = z_offset
    render_front.alpha_composite(head_front, (y + x, x + z))

    render_front = render_front.transform((image_render.width, image_render.height), Image.AFFINE,
                                          (1, 0, 0, 0.5, 45 / 52, -0.5))

    image_render.paste(render_top, (round(-97.5 * scale + 1 / 6), round(-21.65 * scale + 0.254)))
    image_render.alpha_composite(render_right)
    image_render.alpha_composite(render_front)
    image_render.alpha_composite(render_right_head)

    return Render(image_render)


async def render_player_card(*, username: str = None, discord_user: discord.User = None, type: CardType) -> Render:
    player_info = await get_player_info(username=username, discord_user=discord_user)
    player_cosmetics = await get_player_cosmetics(username=username, discord_user=discord_user)
    skin_data = await get_skin(player_info.uuid)
    image_skin = (await render_model(skin_data['skin'], skin_data['slim'], 6)).image

    image_base = Image.new('RGBA', (PLAYER_CARD_WIDTH, PLAYER_CARD_HEIGHT), color=(0, 0, 0, 0))
    draw_base = ImageDraw.Draw(image_base)

    if type == CardType.Prison:
        image_background = Image.open('images/prison.png')
        stats = [('RANK', player_info.stats_prison.rank),
                 ('BLOCKS MINED', get_number_representation(player_info.stats_prison.blocks))]
    elif type == CardType.Infamy:
        image_background = Image.open('images/arena.png')
        stats = [('INFAMY', str(player_info.stats_arena.infamy)), ('KDA', str(player_info.stats_arena.kda))]
    elif type == CardType.Kills:
        image_background = Image.open('images/arena.png')
        stats = [('KILLS', str(player_info.stats_arena.kills)), ('ASSISTS', str(player_info.stats_arena.assists))]
    else:
        raise

    if image_background.width != PLAYER_CARD_WIDTH or image_background.height != PLAYER_CARD_HEIGHT:
        image_background = image_background.resize((PLAYER_CARD_WIDTH, PLAYER_CARD_HEIGHT))

    image_mask = image_base.copy()
    draw_mask = ImageDraw.Draw(image_mask)
    draw_mask.ellipse(
        (-PLAYER_CARD_HEIGHT // 2 - 8 * SPACING, -8 * SPACING, PLAYER_CARD_HEIGHT // 2 + 8 * SPACING,
         PLAYER_CARD_HEIGHT + 8 * SPACING),
        fill=(255, 255, 255, 255))

    image_mask.paste(image_background, mask=image_mask)

    image_card = image_base.copy()
    draw_card = ImageDraw.Draw(image_card)
    draw_card.rounded_rectangle((SPACING, SPACING, PLAYER_CARD_WIDTH - SPACING, PLAYER_CARD_HEIGHT - SPACING),
                                fill=(255, 255, 255, 255), radius=15)

    image_card.paste(image_mask, mask=image_card)

    draw_base.rounded_rectangle((SPACING, SPACING, PLAYER_CARD_WIDTH - SPACING, PLAYER_CARD_HEIGHT - SPACING),
                                fill=(32, 34, 37, 255), radius=15)
    image_base.paste(image_card, mask=image_card)

    image_skin = image_skin.crop((0, 0, image_skin.width, PLAYER_CARD_HEIGHT - 3 * SPACING))

    image_base.paste(image_skin, (5 * SPACING, 2 * SPACING), mask=image_skin)

    font_username = ImageFont.truetype(FONT_BOLD, 36)
    draw_base.text((10 * SPACING + image_skin.width, 3 * SPACING), player_info.username, (235, 235, 235), font_username)

    font_stats_header = ImageFont.truetype(FONT_LIGHT, 18)
    font_stats = ImageFont.truetype(FONT_BLACK, 54)

    draw_base.text((10 * SPACING + image_skin.width, 8 * SPACING), stats[0][0], (192, 192, 192), font_stats_header)
    draw_base.text((10 * SPACING + image_skin.width, 10 * SPACING), stats[0][1], (77, 189, 138), font_stats)

    length_stats_left = draw_base.textlength(stats[0][1], font_stats)

    draw_base.text((14 * SPACING + image_skin.width + max(length_stats_left, 80), 8 * SPACING), stats[1][0],
                   (192, 192, 192), font_stats_header)
    draw_base.text((14 * SPACING + image_skin.width + max(length_stats_left, 80), 10 * SPACING), stats[1][1],
                   (77, 189, 138), font_stats)

    for cosmetic in player_cosmetics:
        if cosmetic.type == CosmeticsType.Title:
            image_ribbon = Image.new('RGBA', (215, 35), color=cosmetic.attributes.get('color', (255, 122, 101, 255)))
            draw_ribbon = ImageDraw.Draw(image_ribbon)

            font_ribbon = ImageFont.truetype(FONT_BLACK if cosmetic.attributes.get('bold', None) else FONT_REGULAR, 18)
            draw_ribbon.text((image_ribbon.width // 2, image_ribbon.height // 2),
                             cosmetic.string, (255, 255, 255, 255), font_ribbon, anchor='mm')

            image_ribbon = image_ribbon.rotate(-35, expand=True).crop((0, 30, 164, PLAYER_CARD_HEIGHT))
            image_base.paste(image_ribbon, (PLAYER_CARD_WIDTH - 175, SPACING), mask=image_ribbon)

    return Render(image_base)


async def render_leaderboard(*, username: str = None, discord_user: discord.User = None,
                             type: LeaderboardType) -> Render:
    async def render_row(player_info: PlayerInfo, position: int) -> Render:
        image_row = Image.new('RGBA', (LEADERBOARD_WIDTH, 100), color=(0, 0, 0, 0))
        draw_row = ImageDraw.Draw(image_row)

        draw_row.rounded_rectangle((0, 0, image_row.width, image_row.height), fill=(32, 34, 37, 255), radius=15)

        bounds_position = draw_row.textbbox((0, 0), f'#{position}', font_position)
        draw_row.text(
            (2 * SPACING + (position_length - bounds_position[2]) // 2,
             (image_row.height - bounds_position[3]) // 2),
            f'#{position}', (214, 214, 214, 255), font_position)

        skin_data = await get_skin(player_info.uuid)
        image_avatar = (await render_avatar(skin_data['skin'], 6)).image

        image_row.paste(image_avatar,
                        (4 * SPACING + position_length, (image_row.height - image_avatar.height) // 2))

        bounds_name = draw_row.textbbox((0, 0), player_info.username, font_stats)
        draw_row.text(
            (6 * SPACING + position_length + image_avatar.width, (image_row.height - bounds_name[3]) // 2),
            player_info.username,
            (212, 175, 55, 255) if target_position != -1 and player_info.username == target_player_info.username else (
                255, 255, 255, 255), font_stats)

        bounds_stats = draw_row.textbbox((0, 0), get_stats(player_info), font_stats)
        draw_row.text((image_row.width - 2 * SPACING - bounds_stats[2], (image_row.height - bounds_stats[3]) // 2),
                      get_stats(player_info), (255, 255, 255, 255), font_stats)

        return Render(image_row)

    if type == LeaderboardType.Rank:
        get_stats = lambda player_info: player_info.stats_prison.rank
    elif type == LeaderboardType.Kda:
        get_stats = lambda player_info: str(player_info.stats_arena.kda)
    elif type == LeaderboardType.Kills:
        get_stats = lambda player_info: get_number_representation(player_info.stats_arena.kills)
    elif type == LeaderboardType.Blocks:
        get_stats = lambda player_info: get_number_representation(player_info.stats_prison.blocks)
    elif type == LeaderboardType.Infamy:
        get_stats = lambda player_info: str(player_info.stats_arena.infamy)
    elif type == LeaderboardType.Deaths:
        get_stats = lambda player_info: get_number_representation(player_info.stats_arena.deaths)
    else:
        raise

    leaderboard = get_leaderboard(type)

    target_position = -1
    if username or discord_user:
        try:
            target_position = await get_position(username=username, discord_user=discord_user, type=type)
            target_player_info = await get_player_info(username=username, discord_user=discord_user, type=type)
        except DiscordNotLinkedError:
            pass

    try:
        leaderboard_highlight = [await leaderboard.__anext__() for i in range(3)]
    except StopAsyncIteration:
        raise NotEnoughDataError()

    image_highlight = Image.new('RGBA', (LEADERBOARD_WIDTH, LEADERBOARD_HEIGHT + SPACING), color=(0, 0, 0, 0))
    draw_highlight = ImageDraw.Draw(image_highlight)

    draw_highlight.rounded_rectangle((0, 0, LEADERBOARD_WIDTH, LEADERBOARD_HEIGHT), fill=(32, 34, 37, 255), radius=15)

    font_title = ImageFont.truetype(FONT_BOLD, 36)
    font_subtitle = ImageFont.truetype(FONT_BOLD, 18)

    bounds_title = draw_highlight.textbbox((0, 56), type.name.upper(), font_title)
    draw_highlight.text(((LEADERBOARD_WIDTH - bounds_title[2]) // 2, 56),
                        type.name.upper(), (255, 255, 255, 255), font_title)

    length_subtitle = draw_highlight.textlength('LEADERBOARD', font_subtitle)
    draw_highlight.text(((LEADERBOARD_WIDTH - length_subtitle) // 2, bounds_title[3] + SPACING),
                        'LEADERBOARD', (255, 255, 255, 255), font_subtitle)

    skin_data_big = await get_skin(leaderboard_highlight[0].uuid)
    image_avatar_big = (await render_avatar(skin_data_big['skin'], 10)).image

    image_highlight.paste(image_avatar_big, (270 - image_avatar_big.width // 2, 177))

    skin_data_two = await get_skin(leaderboard_highlight[1].uuid)
    image_avatar_two = (await render_avatar(skin_data_two['skin'], 7)).image

    image_highlight.paste(image_avatar_two, (93 - image_avatar_two.width // 2, 225))

    skin_data_three = await get_skin(leaderboard_highlight[2].uuid)
    image_avatar_three = (await render_avatar(skin_data_three['skin'], 7)).image

    image_highlight.paste(image_avatar_three, (449 - image_avatar_three.width // 2, 235))

    font_highlight_big = ImageFont.truetype(FONT_BOLD, 24)
    font_highlight_med = ImageFont.truetype(FONT_BOLD, 18)

    length_highlight_big = draw_highlight.textlength(leaderboard_highlight[0].username, font_highlight_big)
    draw_highlight.text((270 - length_highlight_big // 2, 270), leaderboard_highlight[0].username,
                        (212, 175, 55, 255) if target_position != -1 and leaderboard_highlight[
                            0].username == target_player_info.username else (
                            255, 255, 255, 255), font_highlight_big)

    length_highlight_two = draw_highlight.textlength(leaderboard_highlight[1].username, font_highlight_med)
    draw_highlight.text((93 - length_highlight_two // 2, 298), leaderboard_highlight[1].username,
                        (212, 175, 55, 255) if target_position != -1 and leaderboard_highlight[
                            1].username == target_player_info.username else (
                            255, 255, 255, 255), font_highlight_med)

    length_highlight_three = draw_highlight.textlength(leaderboard_highlight[2].username, font_highlight_med)
    draw_highlight.text((449 - length_highlight_three // 2, 308), leaderboard_highlight[2].username,
                        (212, 175, 55, 255) if target_position != -1 and leaderboard_highlight[
                            2].username == target_player_info.username else (
                            255, 255, 255, 255), font_highlight_med)

    draw_highlight.polygon([(210, LEADERBOARD_HEIGHT + SPACING),
                            (163, 392),
                            (495, 392),
                            (452, LEADERBOARD_HEIGHT + SPACING)], fill=(77, 189, 138))
    draw_highlight.polygon([(93, LEADERBOARD_HEIGHT + SPACING),
                            (48, 374),
                            (377, 374),
                            (333, LEADERBOARD_HEIGHT + SPACING)], fill=(94, 207, 149))
    draw_highlight.polygon([(187, LEADERBOARD_HEIGHT + SPACING),
                            (155, 344),
                            (388, 344),
                            (355, LEADERBOARD_HEIGHT + SPACING)], fill=(158, 205, 187))

    font_stats_big = ImageFont.truetype(FONT_BLACK, 48)
    font_stats_med = ImageFont.truetype(FONT_BLACK, 36)

    length_stats_big = draw_highlight.textlength(get_stats(leaderboard_highlight[0]), font_stats_big)
    draw_highlight.text((270 - length_stats_big // 2, 368),
                        get_stats(leaderboard_highlight[0]), (14, 14, 38, 255), font_stats_big)

    length_stats_two = draw_highlight.textlength(get_stats(leaderboard_highlight[1]), font_stats_med)
    draw_highlight.text((117 - length_stats_two // 2, 400),
                        get_stats(leaderboard_highlight[1]), (14, 14, 38, 255), font_stats_med)

    length_stats_three = draw_highlight.textlength(get_stats(leaderboard_highlight[2]), font_stats_med)
    draw_highlight.text((424 - length_stats_three // 2, 415),
                        get_stats(leaderboard_highlight[2]), (14, 14, 38, 255), font_stats_med)

    additional_rows = []

    font_position = ImageFont.truetype(FONT_BLACK, 24)
    font_stats = ImageFont.truetype(FONT_BOLD, 18)

    position_length = max(round(draw_highlight.textlength(f'#{target_position}', font_position)), 4 * SPACING)

    async for i, player_info in a.enumerate(a.islice(leaderboard, 5 if target_position < 8 else 4)):
        additional_rows.append((await render_row(player_info, i + 4)).image)

    if target_position >= 8:
        row_height = 30
        radius = 10

        image_row = Image.new('RGBA', (LEADERBOARD_WIDTH, row_height), color=(0, 0, 0, 0))
        draw_row = ImageDraw.Draw(image_row)
        draw_row.ellipse(
            ((LEADERBOARD_WIDTH - radius) // 2, (row_height - radius) // 2,
             (LEADERBOARD_WIDTH + radius) // 2, (row_height + radius) // 2), fill=(209, 222, 241, 255))
        draw_row.ellipse(
            ((LEADERBOARD_WIDTH - 5 * SPACING - radius) // 2, (row_height - radius) // 2,
             (LEADERBOARD_WIDTH - 5 * SPACING + radius) // 2, (row_height + radius) // 2), fill=(209, 222, 241, 255))
        draw_row.ellipse(
            ((LEADERBOARD_WIDTH + 5 * SPACING - radius) // 2, (row_height - radius) // 2,
             (LEADERBOARD_WIDTH + 5 * SPACING + radius) // 2, (row_height + radius) // 2), fill=(209, 222, 241, 255))

        additional_rows.append(image_row)
        additional_rows.append((await render_row(target_player_info, target_position + 1)).image)

    image_base = Image.new('RGBA', (LEADERBOARD_WIDTH,
                                    LEADERBOARD_HEIGHT + sum(row.height + SPACING for row in additional_rows)),
                           color=(0, 0, 0, 0))
    image_base.paste(image_highlight)

    height = 0
    for row in additional_rows:
        image_base.paste(row, (0, LEADERBOARD_HEIGHT + SPACING + height))
        height += row.height + SPACING

    return Render(image_base)


async def render_xp_card(discord_user: discord.User) -> Render:
    xp = await get_xp(discord_user)

    image_base = Image.new('RGBA', (XP_CARD_WIDTH, XP_CARD_HEIGHT), color=(0, 0, 0, 0))
    draw_base = ImageDraw.Draw(image_base)
    draw_base.rounded_rectangle((SPACING, SPACING, XP_CARD_WIDTH - SPACING, XP_CARD_HEIGHT - SPACING),
                                fill=(32, 34, 37, 255), radius=15)

    font_name = ImageFont.truetype(FONT_BOLD, 36)
    font_discrim = ImageFont.truetype(FONT_LIGHT, 27)

    bounds_name = draw_base.textbbox((0, 0), discord_user.name, font_name)
    draw_base.text((10 * SPACING + 100, 8 * SPACING),
                   discord_user.name, (255, 255, 255, 255), font_name, anchor='ls')

    draw_base.text((11 * SPACING + 100 + bounds_name[2], 8 * SPACING),
                   '#' + discord_user.discriminator, (192, 192, 192, 255), font_discrim, anchor='ls')

    font_stats_header = ImageFont.truetype(FONT_LIGHT, 18)
    font_stats = ImageFont.truetype(FONT_BLACK, 54)

    length_stats_header_left = draw_base.textlength('XP', font_stats_header)
    draw_base.text((10 * SPACING + 100, 7 * SPACING + bounds_name[3]),
                   'XP', (192, 192, 192, 255), font_stats_header)

    length_stats_left = draw_base.textlength(get_number_representation(xp), font_stats)
    draw_base.text((11 * SPACING + 100 + length_stats_header_left, 6 * SPACING + bounds_name[3]),
                   get_number_representation(xp), (77, 189, 138, 255), font_stats)

    length_stats_header_mid = draw_base.textlength('LEVEL', font_stats_header)
    draw_base.text(
        (16 * SPACING + 100 + length_stats_header_left + length_stats_left, 7 * SPACING + bounds_name[3]),
        'LEVEL', (192, 192, 192, 255), font_stats_header)

    length_stats_mid = draw_base.textlength(get_number_representation(get_level_from_xp(xp)), font_stats)
    draw_base.text((17 * SPACING + 100 + length_stats_header_left + length_stats_left + length_stats_header_mid,
                    6 * SPACING + bounds_name[3]),
                   get_number_representation(get_level_from_xp(xp)), (77, 189, 138, 255), font_stats)

    # length_stats_header_right = draw_base.textlength('RANK', font_stats_header)
    # draw_base.text((22 * SPACING + 100 + length_stats_header_left + length_stats_left + length_stats_header_mid + length_stats_mid, 7 * SPACING + bounds_name[3]),
    # 			   'RANK', (192, 192, 192, 255), font_stats_header)
    #
    # draw_base.text((23 * SPACING + 100 + length_stats_header_left + length_stats_left + length_stats_header_mid + length_stats_mid + length_stats_header_right, 6 * SPACING + bounds_name[3]),
    # 			   '#33', (77, 189, 138, 255), font_stats)

    draw_base.ellipse((5 * SPACING - 5, (PLAYER_CARD_HEIGHT - 110) // 2,
                       5 * SPACING + 105, (PLAYER_CARD_HEIGHT + 110) // 2),
                      fill=(26, 26, 26, 255))
    draw_base.pieslice((5 * SPACING - 5, (PLAYER_CARD_HEIGHT - 110) // 2,
                        5 * SPACING + 105, (PLAYER_CARD_HEIGHT + 110) // 2),
                       start=270, end=270 + (xp - get_min_xp_for_level(get_level_from_xp(xp))) / (
                get_min_xp_for_level(get_level_from_xp(xp) + 1) - get_min_xp_for_level(
            get_level_from_xp(xp))) * 360,
                       fill=(77, 189, 138, 255))

    image_mask = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    draw_mask = ImageDraw.Draw(image_mask)
    draw_mask.ellipse((0, 0, 100, 100), fill=(255, 255, 255, 255))

    try:
        image_avatar = Image.open(BytesIO(await discord_user.avatar_url_as(format='gif').read()))
        image_background = Image.new('RGBA', image_base.size, (54, 57, 63, 255))

        frames = []
        for frame in ImageSequence.Iterator(image_avatar):
            image_frame = Image.alpha_composite(image_background, image_base)
            image_frame.paste(frame.resize((100, 100)), (5 * SPACING, (PLAYER_CARD_HEIGHT - 100) // 2),
                              mask=image_mask)
            frames.append(image_frame)

        return Render(*frames)
    except discord.InvalidArgument:
        image_avatar = Image.open(BytesIO(await discord_user.avatar_url_as(format='png').read()))
        image_base.paste(image_avatar.resize((100, 100)), (5 * SPACING, (PLAYER_CARD_HEIGHT - 100) // 2),
                         mask=image_mask)

        return Render(image_base)


async def render_xp_leaderboard(discord_user: discord.User) -> Render:
    async def render_row(discord_user: discord.User, xp: int, position: int) -> Render:
        image_row = Image.new('RGBA', (XP_LEADERBOARD_WIDTH, 75), color=(0, 0, 0, 0))
        draw_row = ImageDraw.Draw(image_row)

        bounds_position = draw_row.textbbox((0, 0), f'#{position}', font_position)
        draw_row.text((2 * SPACING + position_length // 2, image_row.height // 2),
                      f'#{position}', (214, 214, 214, 255), font_position, anchor='mm')

        draw_row.ellipse((4 * SPACING + position_length - 5, 0, 4 * SPACING + position_length + 70, 75),
                         fill=(26, 26, 26, 255))
        draw_row.pieslice((4 * SPACING + position_length - 5, 0, 4 * SPACING + position_length + 70, 75), start=270,
                          end=270 + (xp - get_min_xp_for_level(get_level_from_xp(xp))) / (
                                  get_min_xp_for_level(get_level_from_xp(xp) + 1) - get_min_xp_for_level(
                              get_level_from_xp(xp))) * 360, fill=(77, 189, 138, 255))

        image_mask = Image.new('RGBA', (65, 65), (0, 0, 0, 0))
        draw_mask = ImageDraw.Draw(image_mask)
        draw_mask.ellipse((0, 0, 65, 65), fill=(255, 255, 255, 255))

        image_avatar = Image.open(BytesIO(await discord_user.avatar_url_as(format='png').read()))
        image_row.paste(image_avatar.resize((65, 65)), (4 * SPACING + position_length, 5), mask=image_mask)

        font_name = ImageFont.truetype(FONT_BOLD, 27)
        font_discrim = ImageFont.truetype(FONT_LIGHT, 22)

        length_name = draw_base.textlength(discord_user.name, font_name)
        draw_row.text((7 * SPACING + position_length + 65, (image_row.height + bounds_position[3]) // 2),
                      discord_user.name, (255, 255, 255, 255), font_name, anchor='ls')

        draw_row.text((8 * SPACING + position_length + 65 + length_name, (image_row.height + bounds_position[3]) // 2),
                      '#' + discord_user.discriminator, (192, 192, 192, 255), font_discrim, anchor='ls')

        font_xp = ImageFont.truetype(FONT_BLACK, 27)
        bounds_xp = draw_row.textbbox((0, 0), get_number_representation(xp), font_xp)

        draw_row.text((image_row.width - 2 * SPACING - bounds_xp[2], (image_row.height - bounds_xp[3]) // 2),
                      get_number_representation(xp), (255, 255, 255, 255), font_xp)

        return Render(image_row)

    users = sorted(await get_all_xp(), key=lambda user: user.xp, reverse=True)

    target_user = None
    target_position = -1
    for i, user in enumerate(users):
        if user.discord_id == discord_user.id:
            target_user = user
            target_position = i
            break

    font_position = ImageFont.truetype(FONT_BLACK, 24)

    if target_position < 5:
        image_base = Image.new('RGBA', (XP_LEADERBOARD_WIDTH, 14 * SPACING + 5 * 75), color=(0, 0, 0, 0))
        draw_base = ImageDraw.Draw(image_base)

        position_length = max(round(draw_base.textlength(f'#{target_position}', font_position)), 4 * SPACING)

        draw_base.rounded_rectangle((0, 0, XP_LEADERBOARD_WIDTH, 14 * SPACING + 5 * 75),
                                    fill=(32, 34, 37, 255), radius=15)
    else:
        image_base = Image.new('RGBA', (XP_LEADERBOARD_WIDTH, 16 * SPACING + 5 * 75 + 30), color=(0, 0, 0, 0))
        draw_base = ImageDraw.Draw(image_base)

        position_length = max(round(draw_base.textlength(f'#{target_position}', font_position)), 4 * SPACING)

        draw_base.rounded_rectangle((0, 0, XP_LEADERBOARD_WIDTH, 12 * SPACING + 4 * 75),
                                    fill=(32, 34, 37, 255), radius=15)
        draw_base.rounded_rectangle((0, 12 * SPACING + 4 * 75 + 30, XP_LEADERBOARD_WIDTH, 16 * SPACING + 5 * 75 + 30),
                                    fill=(32, 34, 37, 255), radius=15)

        image_row = (await render_row(discord_user, target_user.xp, target_position + 1)).image
        image_base.paste(image_row, (0, 14 * SPACING + 4 * 75 + 30), mask=image_row)

        image_dots = Image.new('RGBA', (XP_LEADERBOARD_WIDTH, 30), color=(0, 0, 0, 0))
        radius = 10

        draw_dots = ImageDraw.Draw(image_dots)
        draw_dots.ellipse(
            ((XP_LEADERBOARD_WIDTH - radius) // 2, (30 - radius) // 2, (XP_LEADERBOARD_WIDTH + radius) // 2,
             (30 + radius) // 2),
            fill=(209, 222, 241, 255))
        draw_dots.ellipse(
            ((XP_LEADERBOARD_WIDTH - 5 * SPACING - radius) // 2, (30 - radius) // 2,
             (XP_LEADERBOARD_WIDTH - 5 * SPACING + radius) // 2, (30 + radius) // 2),
            fill=(209, 222, 241, 255))
        draw_dots.ellipse(
            ((XP_LEADERBOARD_WIDTH + 5 * SPACING - radius) // 2, (30 - radius) // 2,
             (XP_LEADERBOARD_WIDTH + 5 * SPACING + radius) // 2, (30 + radius) // 2),
            fill=(209, 222, 241, 255))

        image_base.paste(image_dots, (0, 12 * SPACING + 4 * 75), mask=image_dots)

    image_highlight = Image.new('RGBA', (XP_LEADERBOARD_WIDTH, 4 * SPACING + 75), color=(23, 24, 26, 255))
    image_base.paste(image_highlight, mask=image_base.crop((0, 0, image_highlight.width, image_highlight.height)))

    for i in range(min(5 if target_position < 5 else 4, len(users))):
        image_row = (await render_row(bot.utilities.resolve_id(users[i].discord_id), users[i].xp, i + 1)).image
        image_base.paste(image_row, (0, 2 * SPACING) if i == 0 else (0, (4 + 2 * i) * SPACING + i * 75), mask=image_row)

    return Render(image_base)


async def main():
    (await render_player_card(username='keyutedev', type=CardType.Prison)).image.show()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
