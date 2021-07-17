from io import BytesIO

import discord
from PIL import Image, ImageDraw, ImageFont, ImageSequence

from bot.card.Render import Render, Renderable
from bot.card.card import FONT_BLACK, FONT_BOLD, FONT_LIGHT, SPACING
from helpers.utilities import get_number_representation
from helpers.xp import get_level_from_xp, get_min_xp_for_level, get_xp

XP_CARD_WIDTH = 335
XP_CARD_HEIGHT = 400


class XPCard(Renderable):
    def __init__(self, discord_user: discord.User):
        self._discord_user = discord_user

    async def render(self) -> Render:
        xp = await get_xp(self._discord_user)

        image_base = Image.new('RGBA', (XP_CARD_WIDTH, XP_CARD_HEIGHT), color=(0, 0, 0, 0))
        draw_base = ImageDraw.Draw(image_base)
        draw_base.rounded_rectangle((0, 0, XP_CARD_WIDTH, XP_CARD_HEIGHT),
                                    fill=(32, 34, 37, 255), radius=15)

        font_name = ImageFont.truetype(FONT_BOLD, 36)
        font_discrim = ImageFont.truetype(FONT_LIGHT, 27)

        bounds_name = draw_base.textbbox((0, 0), self._discord_user.name, font_name)
        bounds_discrim = draw_base.textbbox((0, 0), '#' + self._discord_user.discriminator, font_discrim)

        draw_base.text(((XP_CARD_WIDTH - bounds_name[2] - bounds_discrim[2] - SPACING // 2) // 2, 11 * SPACING + 100),
                       self._discord_user.name, (255, 255, 255, 255), font_name, anchor='ls')

        draw_base.text(((XP_CARD_WIDTH + bounds_name[2] - bounds_discrim[2] + SPACING // 2) // 2, 11 * SPACING + 100),
                       '#' + self._discord_user.discriminator, (192, 192, 192, 255), font_discrim, anchor='ls')

        font_stats_header = ImageFont.truetype(FONT_LIGHT, 18)
        font_stats = ImageFont.truetype(FONT_BLACK, 54)

        bounds_stats_header_left = draw_base.textbbox((0, 0), 'LEVEL', font_stats_header)
        bounds_stats_header_right = draw_base.textbbox((0, 0), 'XP', font_stats_header)

        length_stats_left = draw_base.textlength(get_number_representation(get_level_from_xp(xp)), font_stats)
        length_stats_right = draw_base.textlength(get_number_representation(xp), font_stats)

        draw_base.text(((XP_CARD_WIDTH
                         - max(bounds_stats_header_right[2], length_stats_right)
                         - 4 * SPACING) // 2,
                        12 * SPACING + 100 + bounds_name[3]),
                       'LEVEL', (192, 192, 192, 255), font_stats_header, anchor='mt')
        draw_base.text(((XP_CARD_WIDTH
                         + max(bounds_stats_header_left[2], length_stats_left)
                         + 4 * SPACING) // 2,
                        12 * SPACING + 100 + bounds_name[3]),
                       'XP', (192, 192, 192, 255), font_stats_header, anchor='mt')

        draw_base.text(((XP_CARD_WIDTH
                         - max(bounds_stats_header_right[2], length_stats_right)
                         - 4 * SPACING) // 2,
                        13 * SPACING + 100 + bounds_name[3] + bounds_stats_header_left[3]),
                       get_number_representation(get_level_from_xp(xp)), (77, 189, 138, 255), font_stats, anchor='mt')
        draw_base.text(((XP_CARD_WIDTH
                         + max(bounds_stats_header_left[2], length_stats_left)
                         + 4 * SPACING) // 2,
                        13 * SPACING + 100 + bounds_name[3] + bounds_stats_header_right[3]),
                       get_number_representation(xp), (77, 189, 138, 255), font_stats, anchor='mt')

        avatar_origin = (XP_CARD_WIDTH // 2, 5 * SPACING + 50)
        draw_base.ellipse((avatar_origin[0] - 55, avatar_origin[1] - 55,
                           avatar_origin[0] + 55, avatar_origin[1] + 55),
                          fill=(26, 26, 26, 255))
        draw_base.pieslice((avatar_origin[0] - 55, avatar_origin[1] - 55,
                            avatar_origin[0] + 55, avatar_origin[1] + 55),
                           start=270, end=270 + (xp - get_min_xp_for_level(get_level_from_xp(xp))) / (
                    get_min_xp_for_level(get_level_from_xp(xp) + 1) - get_min_xp_for_level(
                get_level_from_xp(xp))) * 360,
                           fill=(77, 189, 138, 255))

        image_mask = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        draw_mask = ImageDraw.Draw(image_mask)
        draw_mask.ellipse((0, 0, 100, 100), fill=(255, 255, 255, 255))

        try:
            image_avatar = Image.open(BytesIO(await self._discord_user.avatar_url_as(format='gif').read()))

            frames = []
            for frame in ImageSequence.Iterator(image_avatar):
                image_frame = image_base.copy()
                image_frame.paste(frame.resize((100, 100)), (avatar_origin[0] - 50, avatar_origin[1] - 50),
                                  mask=image_mask)
                frames.append(image_frame)

            return Render(*frames)
        except discord.InvalidArgument:
            image_avatar = Image.open(BytesIO(await self._discord_user.avatar_url_as(format='png').read()))
            image_base.paste(image_avatar.resize((100, 100)), (avatar_origin[0] - 50, avatar_origin[1] - 50),
                             mask=image_mask)

            return Render(image_base)
