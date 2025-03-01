from typing import Iterable, Optional

import nextcord
from PIL import Image, ImageDraw, ImageFont

from bot.api.StreetRunnerApi.Leaderboard import LeaderboardTime
from bot.api.StreetRunnerApi.Player import Player
from bot.api_compatability_layer import get_leaderboard, get_player_info, get_position
from bot.card.Avatar import Avatar
from bot.card.GenericLeaderboard import GenericLeaderboard
from bot.card.Render import Render
from bot.card.card import FONT_BLACK, FONT_BOLD, SPACING
from bot.exceptions import DiscordNotLinkedError
from bot.player.privacy import Privacy
from bot.player.stats import PlayerInfo
from helpers.utilities import get_timedelta_representation


class TimeLeaderboard(GenericLeaderboard):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__()

        self._username = username
        self._discord_user = discord_user

        self._data = get_leaderboard(LeaderboardTime, Privacy.time)

    @property
    async def data(self) -> Iterable[PlayerInfo]:
        return self._leaderboard_data

    @property
    async def target(self) -> Optional[PlayerInfo]:
        return self._target

    @property
    async def target_position(self) -> int:
        return self._target_position

    @property
    async def fill_separator(self) -> bool:
        return True

    async def render_row(self, ctx, player_info) -> Render:
        if ctx['POSITION'] != 1:
            ctx['ROW_HEIGHT'] = 75 + 2 * SPACING

        image_row = Image.new('RGBA', (ctx['ROW_WIDTH'], ctx['ROW_HEIGHT']), color=(0, 0, 0, 0))
        draw_row = ImageDraw.Draw(image_row)

        image_avatar = (await Avatar(await player_info.uuid, 6).render()).image

        length_name = draw_row.textlength(await player_info.username, self._font_stats)
        length_time = draw_row.textlength(get_timedelta_representation(await player_info.time_played), self._font_stats)

        width_required = 16 * SPACING + self._position_length + image_avatar.width + length_name + length_time
        if width_required > image_row.width:
            image_row = Image.new('RGBA', (int(width_required), ctx['ROW_HEIGHT']), color=(0, 0, 0, 0))
            draw_row = ImageDraw.Draw(image_row)

        highlight_color = [
            (212, 175, 55, 255),
            (154, 197, 219, 255),
            (220, 127, 100, 255),
            (214, 214, 214, 255),
        ][min(ctx['POSITION'] - 1, 3)]

        draw_row.text((2 * SPACING + self._position_length, image_row.height // 2),
                      f'#{ctx["POSITION"]}', (214, 214, 214, 255), self._font_position, anchor='rm')

        draw_row.line((5 * SPACING + self._position_length, 0,
                       5 * SPACING + self._position_length, image_row.height),
                      (214, 214, 214, 255))

        draw_row.ellipse((int(4.5 * SPACING) + self._position_length,
                          (image_row.height - SPACING) // 2,
                          int(5.5 * SPACING) + self._position_length,
                          (image_row.height + SPACING) // 2),
                         highlight_color)

        draw_row.arc((4 * SPACING + self._position_length,
                      image_row.height // 2 - SPACING,
                      6 * SPACING + self._position_length,
                      image_row.height // 2 + SPACING),
                     -30, 30, highlight_color)

        draw_row.arc((4 * SPACING + self._position_length,
                      image_row.height // 2 - SPACING,
                      6 * SPACING + self._position_length,
                      image_row.height // 2 + SPACING),
                     150, 210, highlight_color)

        image_row.paste(image_avatar,
                        (8 * SPACING + self._position_length, (image_row.height - image_avatar.height) // 2))

        draw_row.text((10 * SPACING + self._position_length + image_avatar.width, image_row.height // 2),
                      await player_info.username,
                      (212, 175, 55, 255) if self._target_position != -1 and (
                              await player_info.username == await self._target.username) else (
                          255, 255, 255, 255), self._font_stats, anchor='lm')

        draw_row.text((image_row.width - 2 * SPACING, image_row.height // 2),
                      get_timedelta_representation(await player_info.time_played), (255, 255, 255, 255),
                      self._font_stats,
                      anchor='rm')

        return Render(image_row)

    async def render_separator(self, ctx) -> Render:
        image_separator = Image.new('RGBA', (ctx['ROW_WIDTH'], 30), color=(0, 0, 0, 0))
        image_flight = Image.open('images/flight.png').resize((30, 30)).rotate(180)

        image_separator.paste(image_flight, (5 * SPACING + self._position_length - image_flight.width // 2,
                                             (image_separator.height - image_flight.height) // 2), mask=image_flight)

        return Render(image_separator, preferred_height=10)

    async def render(self) -> Render:
        self._target = None
        self._target_position = -1
        if self._username or self._discord_user:
            try:
                if not (await Player({'mc_username': self._username,
                                      'discord_id': self._discord_user.id
                                      }).PlayerPrivacy().data).value & Privacy.time:
                    self._target_position = await get_position(username=self._username, discord_user=self._discord_user,
                                                               leaderboard_type=LeaderboardTime)
                    self._target = await get_player_info(username=self._username, discord_user=self._discord_user)
            except DiscordNotLinkedError:
                pass

        try:
            self._leaderboard_data = [await self._data.__anext__() for i in range(5)]
        except StopAsyncIteration:
            pass

        self._font_position = ImageFont.truetype(FONT_BLACK, 24)
        self._font_stats = ImageFont.truetype(FONT_BOLD, 18)

        self._position_length = max(round(ImageDraw.Draw(Image.new('RGB', (0, 0))).textlength(
            f'#{self._target_position if self._target_position else 0}', self._font_position)), 4 * SPACING)

        return await super().render()
