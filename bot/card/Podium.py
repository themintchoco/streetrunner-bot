from bot.api import *
from bot.card.Avatar import Avatar
from bot.card.card import Render, Renderable, SPACING, FONT_BLACK, FONT_BOLD
from bot.exceptions import *
from helpers.utilities import get_number_representation

LEADERBOARD_PODIUM_WIDTH = 540
LEADERBOARD_PODIUM_HEIGHT = 500


class Podium(Renderable):
    def __init__(self, username: str, discord_user: discord.User, type: LeaderboardType):
        self._username = username
        self._discord_user = discord_user
        self._leaderboard_type = type
        self._data = get_leaderboard(type)

    def get_stats(self, player_info: PlayerInfo) -> str:
        raise NotImplementedError()

    async def render_row(self, player_info: PlayerInfo, position: int) -> Render:
        image_row = Image.new('RGBA', (LEADERBOARD_PODIUM_WIDTH, 100), color=(0, 0, 0, 0))
        draw_row = ImageDraw.Draw(image_row)

        draw_row.rounded_rectangle((0, 0, image_row.width, image_row.height), fill=(32, 34, 37, 255), radius=15)

        bounds_position = draw_row.textbbox((0, 0), f'#{position}', self._font_position)
        draw_row.text(
            (2 * SPACING + (self._position_length - bounds_position[2]) // 2,
             (image_row.height - bounds_position[3]) // 2),
            f'#{position}', (214, 214, 214, 255), self._font_position)

        image_avatar = (await Avatar(player_info.uuid, 6).render()).image

        image_row.paste(image_avatar,
                        (4 * SPACING + self._position_length, (image_row.height - image_avatar.height) // 2))

        bounds_name = draw_row.textbbox((0, 0), player_info.username, self._font_stats)
        draw_row.text(
            (6 * SPACING + self._position_length + image_avatar.width, (image_row.height - bounds_name[3]) // 2),
            player_info.username,
            (212, 175, 55,
             255) if self._target_position != -1 and player_info.username == self._target_player_info.username else (
                255, 255, 255, 255), self._font_stats)

        bounds_stats = draw_row.textbbox((0, 0), self.get_stats(player_info), self._font_stats)
        draw_row.text((image_row.width - 2 * SPACING - bounds_stats[2], (image_row.height - bounds_stats[3]) // 2),
                      self.get_stats(player_info), (255, 255, 255, 255), self._font_stats)

        return Render(image_row)

    async def render(self) -> Render:
        self._target_position = -1
        if self._username or self._discord_user:
            try:
                self._target_position = await get_position(username=self._username, discord_user=self._discord_user,
                                                           type=self._leaderboard_type)
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

        draw_highlight.rounded_rectangle((0, 0, LEADERBOARD_PODIUM_WIDTH, LEADERBOARD_PODIUM_HEIGHT),
                                         fill=(32, 34, 37, 255), radius=15)

        font_title = ImageFont.truetype(FONT_BOLD, 36)
        font_subtitle = ImageFont.truetype(FONT_BOLD, 18)

        bounds_title = draw_highlight.textbbox((0, 56), self._leaderboard_type.name.upper(), font_title)
        draw_highlight.text(((LEADERBOARD_PODIUM_WIDTH - bounds_title[2]) // 2, 56),
                            self._leaderboard_type.name.upper(), (255, 255, 255, 255), font_title)

        length_subtitle = draw_highlight.textlength('LEADERBOARD', font_subtitle)
        draw_highlight.text(((LEADERBOARD_PODIUM_WIDTH - length_subtitle) // 2, bounds_title[3] + SPACING),
                            'LEADERBOARD', (255, 255, 255, 255), font_subtitle)

        image_avatar_big = (await Avatar(leaderboard_highlight[0].uuid, 10).render()).image
        image_highlight.paste(image_avatar_big, (270 - image_avatar_big.width // 2, 177))

        image_avatar_two = (await Avatar(leaderboard_highlight[1].uuid, 7).render()).image
        image_highlight.paste(image_avatar_two, (93 - image_avatar_two.width // 2, 225))

        image_avatar_three = (await Avatar(leaderboard_highlight[2].uuid, 7).render()).image
        image_highlight.paste(image_avatar_three, (449 - image_avatar_three.width // 2, 235))

        font_highlight_big = ImageFont.truetype(FONT_BOLD, 24)
        font_highlight_med = ImageFont.truetype(FONT_BOLD, 18)

        length_highlight_big = draw_highlight.textlength(leaderboard_highlight[0].username, font_highlight_big)
        draw_highlight.text((270 - length_highlight_big // 2, 270), leaderboard_highlight[0].username,
                            (212, 175, 55, 255) if self._target_position != -1 and leaderboard_highlight[
                                0].username == self._target_player_info.username else (
                                255, 255, 255, 255), font_highlight_big)

        length_highlight_two = draw_highlight.textlength(leaderboard_highlight[1].username, font_highlight_med)
        draw_highlight.text((93 - length_highlight_two // 2, 298), leaderboard_highlight[1].username,
                            (212, 175, 55, 255) if self._target_position != -1 and leaderboard_highlight[
                                1].username == self._target_player_info.username else (
                                255, 255, 255, 255), font_highlight_med)

        length_highlight_three = draw_highlight.textlength(leaderboard_highlight[2].username, font_highlight_med)
        draw_highlight.text((449 - length_highlight_three // 2, 308), leaderboard_highlight[2].username,
                            (212, 175, 55, 255) if self._target_position != -1 and leaderboard_highlight[
                                2].username == self._target_player_info.username else (
                                255, 255, 255, 255), font_highlight_med)

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

        length_stats_big = draw_highlight.textlength(self.get_stats(leaderboard_highlight[0]), font_stats_big)
        draw_highlight.text((270 - length_stats_big // 2, 368),
                            self.get_stats(leaderboard_highlight[0]), (14, 14, 38, 255), font_stats_big)

        length_stats_two = draw_highlight.textlength(self.get_stats(leaderboard_highlight[1]), font_stats_med)
        draw_highlight.text((117 - length_stats_two // 2, 400),
                            self.get_stats(leaderboard_highlight[1]), (14, 14, 38, 255), font_stats_med)

        length_stats_three = draw_highlight.textlength(self.get_stats(leaderboard_highlight[2]), font_stats_med)
        draw_highlight.text((424 - length_stats_three // 2, 415),
                            self.get_stats(leaderboard_highlight[2]), (14, 14, 38, 255), font_stats_med)

        additional_rows = []

        self._font_position = ImageFont.truetype(FONT_BLACK, 24)
        self._font_stats = ImageFont.truetype(FONT_BOLD, 18)

        self._position_length = max(round(draw_highlight.textlength(f'#{self._target_position}', self._font_position)),
                                    4 * SPACING)

        async for i, player_info in a.enumerate(a.islice(self._data, 5 if self._target_position < 8 else 4)):
            additional_rows.append((await self.render_row(player_info, i + 4)).image)

        if self._target_position >= 8:
            row_height = 30
            radius = 10

            image_row = Image.new('RGBA', (LEADERBOARD_PODIUM_WIDTH, row_height), color=(0, 0, 0, 0))
            draw_row = ImageDraw.Draw(image_row)
            draw_row.ellipse(
                ((LEADERBOARD_PODIUM_WIDTH - radius) // 2, (row_height - radius) // 2,
                 (LEADERBOARD_PODIUM_WIDTH + radius) // 2, (row_height + radius) // 2), fill=(209, 222, 241, 255))
            draw_row.ellipse(
                ((LEADERBOARD_PODIUM_WIDTH - 5 * SPACING - radius) // 2, (row_height - radius) // 2,
                 (LEADERBOARD_PODIUM_WIDTH - 5 * SPACING + radius) // 2, (row_height + radius) // 2),
                fill=(209, 222, 241, 255))
            draw_row.ellipse(
                ((LEADERBOARD_PODIUM_WIDTH + 5 * SPACING - radius) // 2, (row_height - radius) // 2,
                 (LEADERBOARD_PODIUM_WIDTH + 5 * SPACING + radius) // 2, (row_height + radius) // 2),
                fill=(209, 222, 241, 255))

            additional_rows.append(image_row)
            additional_rows.append((await self.render_row(self._target_player_info, self._target_position + 1)).image)

        image_base = Image.new('RGBA', (LEADERBOARD_PODIUM_WIDTH,
                                        LEADERBOARD_PODIUM_HEIGHT + sum(
                                            row.height + SPACING for row in additional_rows)),
                               color=(0, 0, 0, 0))
        image_base.paste(image_highlight)

        height = 0
        for row in additional_rows:
            image_base.paste(row, (0, LEADERBOARD_PODIUM_HEIGHT + SPACING + height))
            height += row.height + SPACING

        return Render(image_base)


class RankPodium(Podium):
    def __init__(self, username: str = None, discord_user: discord.User = None):
        super().__init__(username, discord_user, LeaderboardType.Rank)

    def get_stats(self, player_info: PlayerInfo) -> str:
        return player_info.stats_prison.rank


class KdaPodium(Podium):
    def __init__(self, username: str = None, discord_user: discord.User = None):
        super().__init__(username, discord_user, LeaderboardType.Kda)

    def get_stats(self, player_info: PlayerInfo) -> str:
        return str(player_info.stats_arena.kda)


class KillsPodium(Podium):
    def __init__(self, username: str = None, discord_user: discord.User = None):
        super().__init__(username, discord_user, LeaderboardType.Kills)

    def get_stats(self, player_info: PlayerInfo) -> str:
        return get_number_representation(player_info.stats_arena.kills)


class BlocksPodium(Podium):
    def __init__(self, username: str = None, discord_user: discord.User = None):
        super().__init__(username, discord_user, LeaderboardType.Blocks)

    def get_stats(self, player_info: PlayerInfo) -> str:
        return get_number_representation(player_info.stats_prison.blocks)


class InfamyPodium(Podium):
    def __init__(self, username: str = None, discord_user: discord.User = None):
        super().__init__(username, discord_user, LeaderboardType.Infamy)

    def get_stats(self, player_info: PlayerInfo) -> str:
        return str(player_info.stats_arena.infamy)


class DeathsPodium(Podium):
    def __init__(self, username: str = None, discord_user: discord.User = None):
        super().__init__(username, discord_user, LeaderboardType.Deaths)

    def get_stats(self, player_info: PlayerInfo) -> str:
        return get_number_representation(player_info.stats_arena.deaths)
