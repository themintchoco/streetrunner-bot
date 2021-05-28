import aiohttp
import asyncio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from bot.RedisClient import RedisClient
import os
import urllib
import base64
import json
import datetime
from enum import Enum

CARD_WIDTH = 640
CARD_HEIGHT = 220

SPACING = 12

FONT_BLACK = 'fonts/Roboto-Black.ttf'
FONT_BOLD = 'fonts/Roboto-Bold.ttf'
FONT_REGULAR = 'fonts/Roboto-Regular.ttf'
FONT_LIGHT = 'fonts/Roboto-Light.ttf'


class UsernameError(ValueError):
	pass


class CardType(Enum):
	Prison, Arena = range(2)


class PlayerStatsType(Enum):
	Prison, Arena = range(2)


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
		self.kda = kwargs['kda']


class PlayerInfo:
	def __init__(self, uuid, username, **kwargs):
		self.uuid = uuid
		self.username = username
		self.stats_prison = kwargs.get('stats_prison', None)
		self.stats_arena = kwargs.get('stats_arena', None)


class Render:
	def __init__(self, image: Image):
		self.image = image

	def file(self, format: str = None) -> BytesIO:
		fp = BytesIO()
		self.image.save(fp, format)
		fp.seek(0)

		return fp


async def get_skin(uuid: str) -> dict:
	client = RedisClient()

	if cached := client.conn.hgetall(f'skins:{uuid}'):
		return {
			'skin': BytesIO(base64.b64decode(cached[b'skin'])),
			'slim': cached[b'slim'] == b'1'
		}

	async with aiohttp.ClientSession() as s:
		async with s.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{urllib.parse.quote(uuid)}') as r:
			if r.status != 200:
				raise
			for prop in (await r.json())['properties']:
				if prop['name'] == 'textures':
					skin_data = json.loads(base64.b64decode(prop['value']))['textures']['SKIN']
					async with s.get(skin_data['url']) as r:
						if r.status != 200:
							raise
						skin = await r.read()

					client.conn.hset(f'skins:{uuid}', mapping={
						'skin': base64.b64encode(skin).decode(),
						'slim': 1 if skin_data.get('metadata', {}).get('model', '') == 'slim' else 0
					})

					client.conn.expire(f'skins:{uuid}', datetime.timedelta(days=1))

					return {
						'skin': BytesIO(skin),
						'slim': skin_data.get('metadata', {}).get('model', '') == 'slim'
					}
			raise


async def get_player_info(username: str, type: PlayerStatsType = None) -> PlayerInfo:
	async with aiohttp.ClientSession() as s:
		async with s.get(
				f'https://streetrunner.dev/api/player?mc_username={urllib.parse.quote(username)}{f"&type={type.name.lower()}" if type else ""}',
				headers={'Authorization': os.environ['API_KEY']}) as r:
			if r.status != 200:
				raise UsernameError({'message': 'The username provided is invalid', 'username': username})
			player_data = await r.json()

	player_stats_prison = None
	player_stats_arena = None

	if prison_data := player_data.get('prison', None):
		player_stats_prison = PlayerStatsPrison(rank=prison_data['rank'], blocks=prison_data['amount'])

	if arena_data := player_data.get('arena', None):
		player_stats_arena = PlayerStatsArena(infamy=arena_data['infamy'], kda=round(
			(arena_data['kills'] + arena_data['assists']) / max(arena_data['deaths'], 1), 2))

	return PlayerInfo(player_data['uuid'], player_data['username'], stats_prison=player_stats_prison,
					  stats_arena=player_stats_arena)


async def render_model(skin, slim: bool, scale: int) -> Render:
	image_render = Image.new('RGBA', (20 * scale, 45 * scale), (0, 0, 0, 0))

	image_skin = Image.open(skin)
	skin_is_old = image_skin.height == 32
	arm_width = 3 if slim else 4

	head_top = image_skin.crop((8, 0, 16, 8)).resize((8 * scale, 8 * scale), Image.NEAREST)
	head_front = image_skin.crop((8, 8, 16, 16)).resize((8 * scale, 8 * scale), Image.NEAREST)
	head_right = image_skin.crop((0, 8, 8, 16)).resize((8 * scale, 8 * scale), Image.NEAREST)

	arm_right_top = image_skin.crop((44, 16, 44 + arm_width, 20)).resize((arm_width * scale, 4 * scale), Image.NEAREST)
	arm_right_front = image_skin.crop((44, 20, 44 + arm_width, 32)).resize((arm_width * scale, 12 * scale),
																		   Image.NEAREST)
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
			body_front.alpha_composite(image_skin.crop((20, 36, 28, 48)).resize((8 * scale, 12 * scale), Image.NEAREST))

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
		y - z + (render_top.width - image_render.width) // 2, x + z + (render_top.height - image_render.height) // 2))

	y = scale * 8
	render_top.alpha_composite(arm_left_top, (
		y - z + (render_top.width - image_render.width) // 2, x + z + (render_top.height - image_render.height) // 2))

	x = x_offset
	y = 0
	z = z_offset
	render_top.alpha_composite(head_top, (
		y - z + (render_top.width - image_render.width) // 2, x + z + (render_top.height - image_render.height) // 2))

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


async def render_card(username: str, card_type: CardType) -> BytesIO:
	player_info = await get_player_info(username)
	skin_data = await get_skin(player_info.uuid)
	image_skin = (await render_model(skin_data['skin'], skin_data['slim'], 6)).image

	image_base = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), color=(0, 0, 0, 0))
	draw_base = ImageDraw.Draw(image_base)

	if card_type == CardType.Prison:
		image_background = Image.open('images/prison.png')
		stats = [('RANK', player_info.stats_prison.rank), ('BLOCKS MINED', str(player_info.stats_prison.blocks))]
	elif card_type == CardType.Arena:
		image_background = Image.open('images/arena.png')
		stats = [('INFAMY', str(player_info.stats_arena.infamy)), ('KDA', str(player_info.stats_arena.kda))]
	else:
		raise

	if image_background.width != CARD_WIDTH or image_background.height != CARD_HEIGHT:
		image_background = image_background.resize((CARD_WIDTH, CARD_HEIGHT))

	image_mask = image_base.copy()
	draw_mask = ImageDraw.Draw(image_mask)
	draw_mask.ellipse((-CARD_HEIGHT // 2 - 8 * SPACING, -8 * SPACING, CARD_HEIGHT // 2 + 8 * SPACING, CARD_HEIGHT + 8 * SPACING), fill=(255, 255, 255, 255))

	image_mask.paste(image_background, mask=image_mask)

	image_card = image_base.copy()
	draw_card = ImageDraw.Draw(image_card)
	draw_card.rounded_rectangle((SPACING, SPACING, CARD_WIDTH - SPACING, CARD_HEIGHT - SPACING),
								fill=(255, 255, 255, 255), radius=15)

	image_card.paste(image_mask, mask=image_card)

	draw_base.rounded_rectangle((SPACING, SPACING, CARD_WIDTH - SPACING, CARD_HEIGHT - SPACING),
								fill=(32, 34, 37, 255), radius=15)
	image_base.paste(image_card, mask=image_card)

	image_skin = image_skin.crop((0, 0, image_skin.width, CARD_HEIGHT - 3 * SPACING))

	image_base.paste(image_skin, (5 * SPACING, 2 * SPACING), mask=image_skin)

	font_username = ImageFont.truetype(FONT_BOLD, 36)
	draw_base.text((10 * SPACING + image_skin.width, 3 * SPACING), player_info.username, (235, 235, 235), font_username)

	font_stats_header = ImageFont.truetype(FONT_LIGHT, 18)
	font_stats = ImageFont.truetype(FONT_BLACK, 54)

	draw_base.text((10 * SPACING + image_skin.width, 8 * SPACING), stats[0][0], (192, 192, 192), font_stats_header)
	draw_base.text((10 * SPACING + image_skin.width, 10 * SPACING), stats[0][1], (77, 189, 138), font_stats)

	length_stats_rank = draw_base.textlength(player_info.stats_prison.rank, font_stats)

	draw_base.text((14 * SPACING + image_skin.width + max(length_stats_rank, 80), 8 * SPACING), stats[1][0],
				   (127, 127, 127), font_stats_header)
	draw_base.text((14 * SPACING + image_skin.width + max(length_stats_rank, 80), 10 * SPACING), stats[1][1],
				   (77, 189, 138), font_stats)

	return Render(image_base)


async def main():
	(await render_card('threeleaves', card_type=CardType.Arena)).image.show()
	# skin_data = await get_skin('1e3cb08c-e29d-478b-a0b9-3b2cacd899bd')
	# image_skin = await gen_render(skin_data['skin'], skin_data['slim'], 6)
	# image_skin.show()


if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
