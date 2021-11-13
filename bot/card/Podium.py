import asyncstdlib as a
import nextcord
from PIL import Image, ImageDraw, ImageFont

import bot.api.StreetRunnerApi.Leaderboard as Leaderboard
from bot.api.StreetRunnerApi.Player import Player
from bot.api_compatability_layer import get_leaderboard, get_player_info, get_position
from bot.card.Avatar import Avatar
from bot.card.Render import Render, Renderable
from bot.card.card import FONT_BLACK, FONT_BOLD, SPACING
from bot.exceptions import DiscordNotLinkedError, NotEnoughDataError
from bot.player.privacy import Privacy
from bot.player.stats import PlayerInfo
from helpers.utilities import get_number_representation

LEADERBOARD_PODIUM_WIDTH = 540
LEADERBOARD_PODIUM_HEIGHT = 500


class Podium(Renderable):
    def __init__(self, username: str, discord_user: nextcord.User, leaderboard_type, display_name='',
                 privacy: Privacy = 0):
        self._username = username
        self._discord_user = discord_user
        self._leaderboard_type = leaderboard_type
        self._display_name = display_name
        self._privacy = privacy
        self._data = get_leaderboard(leaderboard_type, self._privacy)

    async def get_stats(self, player_info: PlayerInfo) -> str:
        raise NotImplementedError()

    async def render_row(self, ctx, player_info: PlayerInfo) -> Render:
        image_row = Image.new('RGBA', (ctx['ROW_WIDTH'], 100), color=(0, 0, 0, 0))
        draw_row = ImageDraw.Draw(image_row)

        image_avatar = (await Avatar(await player_info.uuid, 6).render()).image

        length_name = draw_row.textlength(await player_info.username, self._font_stats)
        length_stats = draw_row.textlength(await self.get_stats(player_info), self._font_stats)

        width_required = 12 * SPACING + self._position_length + image_avatar.width + length_name + length_stats
        if width_required > image_row.width:
            image_row = Image.new('RGBA', (int(width_required), 100), color=(0, 0, 0, 0))
            draw_row = ImageDraw.Draw(image_row)

        draw_row.rounded_rectangle((0, 0, image_row.width, image_row.height), fill=(32, 34, 37, 255), radius=15)

        draw_row.text(
            (2 * SPACING + self._position_length // 2, image_row.height // 2),
            f'#{ctx["POSITION"]}', (214, 214, 214, 255), self._font_position, anchor='mm')

        image_row.paste(image_avatar,
                        (4 * SPACING + self._position_length, (image_row.height - image_avatar.height) // 2))

        draw_row.text((6 * SPACING + self._position_length + image_avatar.width, image_row.height // 2),
                      await player_info.username,
                      (212, 175, 55, 255) if self._target_position != -1 and (await player_info.username) == (
                          await self._target_player_info.username) else (255, 255, 255, 255), self._font_stats,
                      anchor='lm')

        draw_row.text((image_row.width - 2 * SPACING, image_row.height // 2),
                      await self.get_stats(player_info), (255, 255, 255, 255), self._font_stats, anchor='rm')

        return Render(image_row)

    async def render(self) -> Render:
        async def get_rows():
            rows = []

            async for i, player_info in a.enumerate(rows_data):
                rows.append((await self.render_row({**ctx, 'POSITION': i + 4}, player_info)).image)

            if self._target_position >= 8:
                row_height = 30
                radius = 10

                image_row = Image.new('RGBA', (ctx['ROW_WIDTH'], row_height), color=(0, 0, 0, 0))
                draw_row = ImageDraw.Draw(image_row)
                draw_row.ellipse(
                    ((ctx['ROW_WIDTH'] - radius) // 2, (row_height - radius) // 2,
                     (ctx['ROW_WIDTH'] + radius) // 2, (row_height + radius) // 2), fill=(209, 222, 241, 255))
                draw_row.ellipse(
                    ((ctx['ROW_WIDTH'] - 5 * SPACING - radius) // 2, (row_height - radius) // 2,
                     (ctx['ROW_WIDTH'] - 5 * SPACING + radius) // 2, (row_height + radius) // 2),
                    fill=(209, 222, 241, 255))
                draw_row.ellipse(
                    ((ctx['ROW_WIDTH'] + 5 * SPACING - radius) // 2, (row_height - radius) // 2,
                     (ctx['ROW_WIDTH'] + 5 * SPACING + radius) // 2, (row_height + radius) // 2),
                    fill=(209, 222, 241, 255))

                rows.append(image_row)
                rows.append((await self.render_row({**ctx, 'POSITION': self._target_position + 1},
                                                   self._target_player_info)).image)

            return rows

        self._target_position = -1
        if self._username or self._discord_user:
            try:
                if not (await Player({'mc_username': self._username,
                                      'discord_id': self._discord_user.id
                                      }).PlayerPrivacy().data).value & self._privacy:
                    self._target_position = await get_position(username=self._username, discord_user=self._discord_user,
                                                               leaderboard_type=self._leaderboard_type)
                    self._target_player_info = await get_player_info(username=self._username,
                                                                     discord_user=self._discord_user)
            except DiscordNotLinkedError:
                pass

        try:
            leaderboard_highlight = [await self._data.__anext__() for i in range(3)]
        except StopAsyncIteration:
            raise NotEnoughDataError()

        image_highlight = Image.new('RGBA', (LEADERBOARD_PODIUM_WIDTH, LEADERBOARD_PODIUM_HEIGHT + SPACING),
                                    color=(0, 0, 0, 0))
        draw_highlight = ImageDraw.Draw(image_highlight)

        font_title = ImageFont.truetype(FONT_BOLD, 36)
        font_subtitle = ImageFont.truetype(FONT_BOLD, 18)

        bounds_title = draw_highlight.textbbox((0, 56), self._display_name.upper(), font_title)
        draw_highlight.text(((LEADERBOARD_PODIUM_WIDTH - bounds_title[2]) // 2, 56),
                            self._display_name.upper(), (255, 255, 255, 255), font_title)

        length_subtitle = draw_highlight.textlength('LEADERBOARD', font_subtitle)
        draw_highlight.text(((LEADERBOARD_PODIUM_WIDTH - length_subtitle) // 2, bounds_title[3] + SPACING),
                            'LEADERBOARD', (255, 255, 255, 255), font_subtitle)

        image_avatar_big = (await Avatar(await leaderboard_highlight[0].uuid, 10).render()).image
        image_highlight.paste(image_avatar_big, (270 - image_avatar_big.width // 2, 177))

        image_avatar_two = (await Avatar(await leaderboard_highlight[1].uuid, 7).render()).image
        image_highlight.paste(image_avatar_two, (93 - image_avatar_two.width // 2, 225))

        image_avatar_three = (await Avatar(await leaderboard_highlight[2].uuid, 7).render()).image
        image_highlight.paste(image_avatar_three, (449 - image_avatar_three.width // 2, 235))

        font_highlight_big = ImageFont.truetype(FONT_BOLD, 24)
        font_highlight_med = ImageFont.truetype(FONT_BOLD, 18)

        draw_highlight.text((270, 270), await leaderboard_highlight[0].username,
                            (212, 175, 55, 255) if self._target_position != -1 and (
                                await leaderboard_highlight[0].username) == (
                                                       await self._target_player_info.username) else (
                                255, 255, 255, 255), font_highlight_big, anchor='mt')

        draw_highlight.text((93, 298), await leaderboard_highlight[1].username,
                            (212, 175, 55, 255) if self._target_position != -1 and (
                                await leaderboard_highlight[1].username) == (
                                                       await self._target_player_info.username) else (
                                255, 255, 255, 255), font_highlight_med, anchor='mt')

        draw_highlight.text((449, 308), await leaderboard_highlight[2].username,
                            (212, 175, 55, 255) if self._target_position != -1 and (
                                await leaderboard_highlight[2].username) == (
                                                       await self._target_player_info.username) else (
                                255, 255, 255, 255), font_highlight_med, anchor='mt')

        draw_highlight.polygon([(210, LEADERBOARD_PODIUM_HEIGHT + SPACING),
                                (163, 392),
                                (495, 392),
                                (452, LEADERBOARD_PODIUM_HEIGHT + SPACING)], fill=(77, 189, 138))
        draw_highlight.polygon([(93, LEADERBOARD_PODIUM_HEIGHT + SPACING),
                                (48, 374),
                                (377, 374),
                                (333, LEADERBOARD_PODIUM_HEIGHT + SPACING)], fill=(94, 207, 149))
        draw_highlight.polygon([(187, LEADERBOARD_PODIUM_HEIGHT + SPACING),
                                (155, 344),
                                (388, 344),
                                (355, LEADERBOARD_PODIUM_HEIGHT + SPACING)], fill=(158, 205, 187))

        font_stats_big = ImageFont.truetype(FONT_BLACK, 48)
        font_stats_med = ImageFont.truetype(FONT_BLACK, 36)

        length_stats_big = draw_highlight.textlength(await self.get_stats(leaderboard_highlight[0]), font_stats_big)
        draw_highlight.text((270 - length_stats_big // 2, 368),
                            await self.get_stats(leaderboard_highlight[0]), (14, 14, 38, 255), font_stats_big)

        length_stats_two = draw_highlight.textlength(await self.get_stats(leaderboard_highlight[1]), font_stats_med)
        draw_highlight.text((117 - length_stats_two // 2, 400),
                            await self.get_stats(leaderboard_highlight[1]), (14, 14, 38, 255), font_stats_med)

        length_stats_three = draw_highlight.textlength(await self.get_stats(leaderboard_highlight[2]), font_stats_med)
        draw_highlight.text((424 - length_stats_three // 2, 415),
                            await self.get_stats(leaderboard_highlight[2]), (14, 14, 38, 255), font_stats_med)

        self._font_position = ImageFont.truetype(FONT_BLACK, 24)
        self._font_stats = ImageFont.truetype(FONT_BOLD, 18)

        self._position_length = max(round(draw_highlight.textlength(f'#{self._target_position}', self._font_position)),
                                    4 * SPACING)

        ctx = {'ROW_WIDTH': image_highlight.width}
        rows_data = [x async for x in a.islice(self._data, 5 if self._target_position < 8 else 4)]
        rows = await get_rows()

        rows_width = max(row.width for row in rows)
        if rows_width > ctx['ROW_WIDTH']:
            ctx['ROW_WIDTH'] = rows_width
            rows = await get_rows()

        image_base = Image.new('RGBA', (rows_width,
                                        LEADERBOARD_PODIUM_HEIGHT + sum(row.height + SPACING for row in rows)),
                               color=(0, 0, 0, 0))

        draw_base = ImageDraw.Draw(image_base)
        draw_base.rounded_rectangle((0, 0, rows_width, LEADERBOARD_PODIUM_HEIGHT),
                                    fill=(32, 34, 37, 255), radius=15)

        image_base.paste(image_highlight, ((rows_width - image_highlight.width) // 2, 0), mask=image_highlight)

        height = 0
        for row in rows:
            image_base.paste(row, (0, LEADERBOARD_PODIUM_HEIGHT + SPACING + height))
            height += row.height + SPACING

        return Render(image_base)


class RankPodium(Podium):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, Leaderboard.LeaderboardRank, 'Rank', Privacy.prison)

    async def get_stats(self, player_info: PlayerInfo) -> str:
        return (await player_info.stats_prison).rank


class KdaPodium(Podium):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, Leaderboard.LeaderboardKda, 'Kda', Privacy.arena)

    async def get_stats(self, player_info: PlayerInfo) -> str:
        return '{:.2f}'.format((await player_info.stats_arena).kda)


class KillsPodium(Podium):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, Leaderboard.LeaderboardKills, 'Kills', Privacy.arena)

    async def get_stats(self, player_info: PlayerInfo) -> str:
        return get_number_representation((await player_info.stats_arena).kills)


class BlocksPodium(Podium):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, Leaderboard.LeaderboardBlocks, 'Blocks', Privacy.prison)

    async def get_stats(self, player_info: PlayerInfo) -> str:
        return get_number_representation((await player_info.stats_prison).blocks)


class InfamyPodium(Podium):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, Leaderboard.LeaderboardInfamy, 'Infamy', Privacy.arena)

    async def get_stats(self, player_info: PlayerInfo) -> str:
        return str((await player_info.stats_arena).infamy)


class DeathsPodium(Podium):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, Leaderboard.LeaderboardDeaths, 'Deaths', Privacy.arena)

    async def get_stats(self, player_info: PlayerInfo) -> str:
        return get_number_representation((await player_info.stats_arena).deaths)
