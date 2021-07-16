import asyncio
import os
import urllib
from typing import AsyncGenerator

import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFont

from bot.api import get_skin
from bot.card.Render import Render
from bot.exceptions import UsernameError, DiscordNotLinkedError, NotEnoughDataError
from bot.player.stats import PlayerInfo
from card import *
from helpers.utilities import get_number_representation


async def get_event_leaderboard() -> AsyncGenerator[dict, None]:
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://streetrunner.dev/api/tournament/',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status != 200:
                raise
            leaderboard_data = await r.json()

    for player_data in leaderboard_data:
        yield {
            'player': PlayerInfo(player_data['player']['uuid'], player_data['player']['username']),
            'points': player_data['points'],
            'position': player_data['position']
        }


async def get_event_player(*, username: str = None, discord_user: discord.User = None) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://streetrunner.dev/api/tournament/player/?{("mc_username=" + urllib.parse.quote(username)) if username else ("discord_id=" + urllib.parse.quote(str(discord_user.id)))}',
                headers={'Authorization': os.environ['API_KEY']}) as r:
            if r.status == 404:
                raise UsernameError({'message': f'The username provided is invalid',
                                     'username': username}) if username else DiscordNotLinkedError()
            elif r.status != 200:
                raise
            player_data = await r.json()

    return {
        'player': PlayerInfo(player_data['player']['uuid'], player_data['player']['username']),
        'points': player_data['points'],
        'position': player_data['position']
    }


async def render_event_leaderboard(*, username: str = None, discord_user: discord.User = None) -> Render:
    async def render_row(player_data: dict, position: int) -> Render:
        player_info = player_data['player']

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
            (212, 175, 55, 255) if target_position != -1 and player_info.username == target_player_data[
                'player'].username else (255, 255, 255, 255), font_stats)

        bounds_stats = draw_row.textbbox((0, 0), get_stats(player_data), font_stats)
        draw_row.text((image_row.width - 2 * SPACING - bounds_stats[2], (image_row.height - bounds_stats[3]) // 2),
                      get_stats(player_data), (255, 255, 255, 255), font_stats)

        return Render(image_row)

    def get_stats(player_data):
        return get_number_representation(player_data['points'])

    leaderboard = get_event_leaderboard()

    target_position = -1
    if username or discord_user:
        try:
            target_player_data = await get_event_player(username=username, discord_user=discord_user)
            target_position = target_player_data['position']
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

    bounds_title = draw_highlight.textbbox((0, 56), 'TOURNAMENT', font_title)
    draw_highlight.text(((LEADERBOARD_WIDTH - bounds_title[2]) // 2, 56),
                        'TOURNAMENT', (255, 255, 255, 255), font_title)

    length_subtitle = draw_highlight.textlength('LEADERBOARD', font_subtitle)
    draw_highlight.text(((LEADERBOARD_WIDTH - length_subtitle) // 2, bounds_title[3] + SPACING),
                        'LEADERBOARD', (255, 255, 255, 255), font_subtitle)

    skin_data_big = await get_skin(leaderboard_highlight[0]['player'].uuid)
    image_avatar_big = (await render_avatar(skin_data_big['skin'], 10)).image

    image_highlight.paste(image_avatar_big, (270 - image_avatar_big.width // 2, 177))

    skin_data_two = await get_skin(leaderboard_highlight[1]['player'].uuid)
    image_avatar_two = (await render_avatar(skin_data_two['skin'], 7)).image

    image_highlight.paste(image_avatar_two, (93 - image_avatar_two.width // 2, 225))

    skin_data_three = await get_skin(leaderboard_highlight[2]['player'].uuid)
    image_avatar_three = (await render_avatar(skin_data_three['skin'], 7)).image

    image_highlight.paste(image_avatar_three, (449 - image_avatar_three.width // 2, 235))

    font_highlight_big = ImageFont.truetype(FONT_BOLD, 24)
    font_highlight_med = ImageFont.truetype(FONT_BOLD, 18)

    length_highlight_big = draw_highlight.textlength(leaderboard_highlight[0]['player'].username, font_highlight_big)
    draw_highlight.text((270 - length_highlight_big // 2, 270), leaderboard_highlight[0]['player'].username,
                        (212, 175, 55, 255) if target_position != -1 and leaderboard_highlight[
                            0]['player'].username == target_player_data['player'].username else (
                            255, 255, 255, 255), font_highlight_big)

    length_highlight_two = draw_highlight.textlength(leaderboard_highlight[1]['player'].username, font_highlight_med)
    draw_highlight.text((93 - length_highlight_two // 2, 298), leaderboard_highlight[1]['player'].username,
                        (212, 175, 55, 255) if target_position != -1 and leaderboard_highlight[
                            1]['player'].username == target_player_data['player'].username else (
                            255, 255, 255, 255), font_highlight_med)

    length_highlight_three = draw_highlight.textlength(leaderboard_highlight[2]['player'].username, font_highlight_med)
    draw_highlight.text((449 - length_highlight_three // 2, 308), leaderboard_highlight[2]['player'].username,
                        (212, 175, 55, 255) if target_position != -1 and leaderboard_highlight[
                            2]['player'].username == target_player_data['player'].username else (
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

    async for i, player_data in a.enumerate(a.islice(leaderboard, 5 if target_position < 8 else 4)):
        additional_rows.append((await render_row(player_data, i + 4)).image)

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
        additional_rows.append((await render_row(target_player_data, target_position + 1)).image)

    image_base = Image.new('RGBA', (LEADERBOARD_WIDTH,
                                    LEADERBOARD_HEIGHT + sum(row.height + SPACING for row in additional_rows)),
                           color=(0, 0, 0, 0))
    image_base.paste(image_highlight)

    height = 0
    for row in additional_rows:
        image_base.paste(row, (0, LEADERBOARD_HEIGHT + SPACING + height))
        height += row.height + SPACING

    return Render(image_base)


async def main():
    (await render_event_leaderboard(username='threeleaves')).image.show()


if __name__ == '__main__':
    asyncio.run(main())
