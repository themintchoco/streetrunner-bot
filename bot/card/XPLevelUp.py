from PIL import Image, ImageDraw, ImageFont

from bot.api import *
from bot.card.card import SPACING, FONT_BLACK, FONT_BOLD, FONT_LIGHT
from bot.card.Render import Render, Renderable

XP_LEVELUP_WIDTH = 580


class XPLevelUp(Renderable):
    def __init__(self, discord_user: discord.User, level_before: int, level_after: int):
        self._discord_user = discord_user
        self._level_before = level_before
        self._level_after = level_after

    async def render(self) -> Render:
        def get_arrow_position(t):
            if t < 10:
                return get_from_linear_eqn(0, 10, 0, 0.45, t)
            elif t < 20:
                return get_from_linear_eqn(10, 20, 0.45, 0.55, t)
            else:
                return get_from_linear_eqn(20, 30, 0.55, 1, t)

        def get_old_level_position(t):
            return get_from_linear_eqn(0, 10, 0.5, 1, t)

        def get_new_level_position(t):
            return get_from_linear_eqn(20, 30, 0, 0.5, t)

        def get_from_linear_eqn(x1, x2, y1, y2, x):
            return (y1 - y2) / (x1 - x2) * (x - x1) + y1

        def get_animated_avatar_frames(avatar):
            reset = False
            while True:
                try:
                    avatar.seek(0 if reset else avatar.tell() + 1)
                except EOFError:
                    avatar.seek(0)
                reset = yield avatar

        image_base = Image.new('RGBA', (XP_LEVELUP_WIDTH, 100), color=(0, 0, 0, 0))
        draw_base = ImageDraw.Draw(image_base)
        draw_base.rounded_rectangle((0, 0, XP_LEVELUP_WIDTH, 100), fill=(32, 34, 37, 255), radius=15)

        image_mask = Image.new('RGBA', (65, 65), (0, 0, 0, 0))
        draw_mask = ImageDraw.Draw(image_mask)
        draw_mask.ellipse((0, 0, 65, 65), fill=(255, 255, 255, 255))

        try:
            image_avatar = Image.open(BytesIO(await self._discord_user.avatar_url_as(format='gif').read()))
            avatar_frames = get_animated_avatar_frames(image_avatar)
            animated_avatar = True
        except discord.InvalidArgument:
            image_avatar = Image.open(BytesIO(await self._discord_user.avatar_url_as(format='png').read()))
            image_base.paste(image_avatar.resize((65, 65)), (2 * SPACING, (image_base.height - 65) // 2),
                             mask=image_mask)
            animated_avatar = False

        font_name = ImageFont.truetype(FONT_BOLD, 27)
        font_discrim = ImageFont.truetype(FONT_LIGHT, 22)

        length_name = draw_base.textlength(self._discord_user.name, font_name)
        draw_base.text((5 * SPACING + 65, (image_base.height + SPACING) // 2),
                       self._discord_user.name, (255, 255, 255, 255), font_name, anchor='ls')

        draw_base.text((6 * SPACING + 65 + length_name, (image_base.height + SPACING) // 2),
                       '#' + self._discord_user.discriminator, (192, 192, 192, 255), font_discrim, anchor='ls')

        image_arrow = Image.new('RGBA', (30, 30), (0, 0, 0, 0))
        draw_arrow = ImageDraw.Draw(image_arrow)

        draw_arrow.polygon([(0, 20), (15, 0), (30, 20)], fill=(77, 189, 138, 255))
        draw_arrow.rectangle((10, 20, 20, 30), fill=(77, 189, 138, 255))

        font_level = ImageFont.truetype(FONT_BLACK, 24)

        bounds_level_label = draw_base.textbbox((0, 0), 'LEVEL ', font_level)
        bounds_level = draw_base.textbbox((0, 0), str(self._level_after), font_level)

        draw_base.text(
            (image_base.width - 2 * SPACING - max(bounds_level[2], image_arrow.width), image_base.height // 2),
            'LEVEL ', (77, 189, 138, 255), font_level, anchor='rm')

        frames = []
        for t in range(31):
            frame = image_base.copy()
            draw_frame = ImageDraw.Draw(frame)

            if animated_avatar:
                frame.paste((next(avatar_frames) if t < 30 else avatar_frames.send(True)).resize((65, 65)),
                            (2 * SPACING, (image_base.height - 65) // 2), mask=image_mask)

            frame.paste(image_arrow, (
                image_base.width - 2 * SPACING - (max(bounds_level[2], image_arrow.width) + image_arrow.width) // 2,
                int(get_arrow_position(t) * -(image_arrow.height + image_base.height) + image_base.height)),
                        mask=image_arrow)
            draw_frame.text(
                (image_base.width - 2 * SPACING - max(bounds_level[2], image_arrow.width) // 2,
                 int((1 - get_old_level_position(t)) * image_base.height)),
                str(self._level_before), (77, 189, 138, 255), font_level, anchor='mm')
            draw_frame.text((image_base.width - 2 * SPACING - max(bounds_level[2], image_arrow.width) // 2,
                             int((1 - get_new_level_position(t)) * image_base.height)),
                            str(self._level_after), (77, 189, 138, 255), font_level, anchor='mm')

            frames.append(frame)

        return Render(*frames)
