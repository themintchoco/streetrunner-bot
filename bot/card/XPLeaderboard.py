from typing import Iterable, Optional

from bot.api import *
from bot.card.GenericLeaderboard import GenericLeaderboard
from bot.card.card import SPACING, FONT_BLACK, FONT_BOLD, FONT_LIGHT
from bot.card.Render import Render
from bot.player.stats import PlayerInfo
from helpers.utilities import get_number_representation
from helpers.xp import get_level_from_xp, get_min_xp_for_level, get_all_xp


class XPLeaderboard(GenericLeaderboard):
    def __init__(self, discord_user: discord.User = None):
        super().__init__()
        self._discord_user = discord_user

    @property
    async def data(self) -> Iterable[PlayerInfo]:
        return self._data

    @property
    async def target(self) -> Optional[PlayerInfo]:
        return self._target

    @property
    async def target_position(self) -> int:
        return self._target_position

    async def render_row(self, ctx, user) -> Render:
        discord_user = helpers.utilities.resolve_id(user.discord_id)

        image_row = Image.new('RGBA', (ctx['ROW_WIDTH'], ctx['ROW_HEIGHT']), color=(0, 0, 0, 0))
        draw_row = ImageDraw.Draw(image_row)

        bounds_position = draw_row.textbbox((0, 0), f'#{ctx["POSITION"]}', self._font_position)
        draw_row.text((2 * SPACING + self._position_length // 2, image_row.height // 2),
                      f'#{ctx["POSITION"]}', (214, 214, 214, 255), self._font_position, anchor='mm')

        draw_row.ellipse((4 * SPACING + self._position_length - 5,
                          (image_row.height - 75) // 2,
                          4 * SPACING + self._position_length + 70,
                          (image_row.height + 75) // 2),
                         fill=(26, 26, 26, 255))
        draw_row.pieslice((4 * SPACING + self._position_length - 5,
                           (image_row.height - 75) // 2,
                           4 * SPACING + self._position_length + 70,
                           (image_row.height + 75) // 2), start=270,
                          end=270 + (user.xp - get_min_xp_for_level(get_level_from_xp(user.xp))) / (
                                  get_min_xp_for_level(get_level_from_xp(user.xp) + 1) - get_min_xp_for_level(
                              get_level_from_xp(user.xp))) * 360, fill=(77, 189, 138, 255))

        image_mask = Image.new('RGBA', (65, 65), (0, 0, 0, 0))
        draw_mask = ImageDraw.Draw(image_mask)
        draw_mask.ellipse((0, 0, 65, 65), fill=(255, 255, 255, 255))

        image_avatar = Image.open(BytesIO(await discord_user.avatar_url_as(format='png').read()))
        image_row.paste(image_avatar.resize((65, 65)),
                        (4 * SPACING + self._position_length, (image_row.height - 65) // 2),
                        mask=image_mask)

        font_name = ImageFont.truetype(FONT_BOLD, 27)
        font_discrim = ImageFont.truetype(FONT_LIGHT, 22)

        length_name = draw_row.textlength(discord_user.name, font_name)
        draw_row.text((7 * SPACING + self._position_length + 65, (image_row.height + bounds_position[3]) // 2),
                      discord_user.name,
                      (212, 175, 55, 255) if self._target and self._target.discord_id == discord_user.id else (
                          255, 255, 255, 255), font_name, anchor='ls')

        draw_row.text(
            (8 * SPACING + self._position_length + 65 + length_name, (image_row.height + bounds_position[3]) // 2),
            '#' + discord_user.discriminator, (192, 192, 192, 255), font_discrim, anchor='ls')

        font_xp = ImageFont.truetype(FONT_BLACK, 27)
        bounds_xp = draw_row.textbbox((0, 0), get_number_representation(user.xp), font_xp)

        draw_row.text((image_row.width - 2 * SPACING - bounds_xp[2], (image_row.height - bounds_xp[3]) // 2),
                      get_number_representation(user.xp), (255, 255, 255, 255), font_xp)

        return Render(image_row)

    async def render(self) -> Render:
        self._data = sorted(await get_all_xp(), key=lambda user: user.xp, reverse=True)

        self._target = None
        self._target_position = -1
        for i, user in enumerate(self._data):
            if user.discord_id == self._discord_user.id:
                self._target = user
                self._target_position = i
                break

        self._font_position = ImageFont.truetype(FONT_BLACK, 24)

        self._position_length = max(round(ImageDraw.Draw(Image.new('RGB', (0, 0))).textlength(
            f'#{self._target_position if self._target_position else 0}', self._font_position)), 4 * SPACING)

        return await super().render()
