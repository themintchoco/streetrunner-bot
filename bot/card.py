import aiohttp
import asyncio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

import random
import string

CARD_WIDTH = 640
CARD_HEIGHT = 220

SPACING = 12

FONT_BOLD = 'fonts/Roboto-Black.ttf'
FONT_REGULAR = 'fonts/Roboto-Regular.ttf'


async def get_skin(username: str) -> BytesIO:
	async with aiohttp.ClientSession() as s:
		async with s.get('https://api.mojang.com/users/profiles/minecraft/' + username) as r:
			async with s.get('https://crafatar.com/renders/body/' + (await r.json())['id'] + '?overlay') as r:
				skin = await r.read()

	return BytesIO(skin)


async def get_stats(username: str) -> dict:
	# async with aiohttp.ClientSession() as s:
	# 	async with s.get('https://streetrunner.dev/api/player?mc_username=' + username, headers={'Authorization': os.environ['API_KEY']}) as r:
	# 		player = await r.json()
	#
	# return {
	# 	'rank': player['rank'],
	# 	'kda': round((player['stats'][0] + player['stats'][1]) / player['stats'][2], 2)
	# }
	return {
		'rank': ('' if (r := random.randint(0, 5)) == 0 else str(r)) + random.choice(string.ascii_uppercase),
		'kda': round(random.uniform(0.5, 1.5), 2)
	}


async def gen_card(username: str) -> BytesIO:
	image_base = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), color=(0, 0, 0, 0))

	draw_base = ImageDraw.Draw(image_base)
	draw_base.rounded_rectangle((SPACING, SPACING, CARD_WIDTH - SPACING, CARD_HEIGHT - SPACING), fill=(32, 34, 37, 255), radius=15)

	skin = await get_skin(username)

	image_skin = Image.open(skin)
	image_skin = image_skin.crop((0, 0, image_skin.width, CARD_HEIGHT - 3 * SPACING))

	image_base.paste(image_skin, (5 * SPACING, 2 * SPACING), mask=image_skin)

	font_username = ImageFont.truetype(FONT_REGULAR, 24)
	draw_base.text((9 * SPACING + image_skin.width, 3 * SPACING), username, (77, 190, 138), font_username)

	stats = await get_stats(username)

	font_stats_header = ImageFont.truetype(FONT_REGULAR, 18)
	font_stats = ImageFont.truetype(FONT_BOLD, 64)

	draw_base.text((9 * SPACING + image_skin.width, 5 * SPACING + 24), 'RANK', (127, 127, 127), font_stats_header)
	draw_base.text((9 * SPACING + image_skin.width, 6 * SPACING + 24 + 18), stats['rank'], (252, 234, 168), font_stats)

	length_stats_rank = draw_base.textlength(stats['rank'], font_stats)

	draw_base.text((13 * SPACING + image_skin.width + max(length_stats_rank, 100), 5 * SPACING + 24), 'KDA', (127, 127, 127), font_stats_header)
	draw_base.text((13 * SPACING + image_skin.width + max(length_stats_rank, 100), 6 * SPACING + 24 + 18), str(stats['kda']), (252, 234, 168), font_stats)

	fp = BytesIO()
	image_base.save(fp, format='PNG')
	fp.seek(0)

	return fp


async def main():
	image = await gen_card('threeleaves')
	image.show()


if __name__ ==  '__main__':
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())