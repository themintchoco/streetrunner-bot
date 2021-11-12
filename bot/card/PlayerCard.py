import random
from typing import List, Tuple

import nextcord
from PIL import Image, ImageDraw, ImageFont

from bot.api_compatability_layer import get_player_cosmetics, get_player_info
from bot.card.PlayerModel import PlayerModel
from bot.card.Render import Render, Renderable
from bot.card.card import FONT_BLACK, FONT_BOLD, FONT_LIGHT, FONT_REGULAR, SPACING
from bot.cosmetics.cosmetics import CosmeticsType
from bot.player.stats import PlayerInfo
from helpers.utilities import get_number_representation, get_timedelta_representation

PLAYER_CARD_WIDTH = 640
PLAYER_CARD_HEIGHT = 220


class PlayerCard(Renderable):
    def __init__(self, username: str, discord_user: nextcord.User, background: str):
        self._username = username
        self._discord_user = discord_user
        self._background = background

    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str]]:
        raise NotImplementedError()

    async def render_ribbon(self, string, bold, color) -> Render:
        image_ribbon = Image.new('RGBA', (215, 35), color=tuple(int(i * 255) for i in color.rgb))
        draw_ribbon = ImageDraw.Draw(image_ribbon)

        font_ribbon = ImageFont.truetype(FONT_BLACK if bold else FONT_REGULAR, 18)
        draw_ribbon.text((image_ribbon.width // 2, image_ribbon.height // 2),
                         string, (255, 255, 255, 255), font_ribbon, anchor='mm')

        return image_ribbon.rotate(-35, expand=True).crop((0, 30, 164, PLAYER_CARD_HEIGHT))

    async def render(self) -> Render:
        player_info = await get_player_info(username=self._username, discord_user=self._discord_user)
        player_cosmetics = await get_player_cosmetics(username=self._username, discord_user=self._discord_user)
        image_skin = (await PlayerModel(await player_info.uuid, 6).render()).image
        stats = await self.get_stats(player_info)

        image_base = Image.new('RGBA', (PLAYER_CARD_WIDTH, PLAYER_CARD_HEIGHT), color=(0, 0, 0, 0))
        draw_base = ImageDraw.Draw(image_base)

        font_username = ImageFont.truetype(FONT_BOLD, 36)
        font_stats_header = ImageFont.truetype(FONT_LIGHT, 18)
        font_stats = ImageFont.truetype(FONT_BLACK, 54)

        length_name = draw_base.textlength(await player_info.username, font_username)

        width_required = 12 * SPACING + image_skin.width + length_name
        for cosmetic in player_cosmetics:
            if cosmetic.type == CosmeticsType.Title:
                width_required += 135

        if width_required > image_base.width:
            image_base = Image.new('RGBA', (int(width_required), PLAYER_CARD_HEIGHT), color=(0, 0, 0, 0))
            draw_base = ImageDraw.Draw(image_base)

        image_background = image_base.copy()
        image_background.paste(Image.open(self._background))

        image_mask = image_base.copy()
        draw_mask = ImageDraw.Draw(image_mask)
        draw_mask.ellipse(
            (-PLAYER_CARD_HEIGHT // 2 - 8 * SPACING, -8 * SPACING, PLAYER_CARD_HEIGHT // 2 + 8 * SPACING,
             PLAYER_CARD_HEIGHT + 8 * SPACING),
            fill=(255, 255, 255, 255))

        image_mask.paste(image_background, (0, 0), mask=image_mask)

        image_card = image_base.copy()
        draw_card = ImageDraw.Draw(image_card)
        draw_card.rounded_rectangle((SPACING, SPACING, image_base.width - SPACING, image_base.height - SPACING),
                                    fill=(255, 255, 255, 255), radius=15)

        image_card.paste(image_mask, (0, 0), mask=image_card)

        draw_base.rounded_rectangle((SPACING, SPACING, image_base.width - SPACING, image_base.height - SPACING),
                                    fill=(32, 34, 37, 255), radius=15)
        image_base.paste(image_card, mask=image_card)

        image_skin = image_skin.crop((0, 0, image_skin.width, PLAYER_CARD_HEIGHT - 3 * SPACING))

        image_base.paste(image_skin, (5 * SPACING, 2 * SPACING), mask=image_skin)

        draw_base.text((10 * SPACING + image_skin.width, 3 * SPACING), await player_info.username, (235, 235, 235),
                       font_username)

        draw_base.text((10 * SPACING + image_skin.width, 8 * SPACING), stats[0][0], (192, 192, 192), font_stats_header)
        draw_base.text((10 * SPACING + image_skin.width, 10 * SPACING), stats[0][1], (77, 189, 138), font_stats)

        length_stats_left = draw_base.textlength(stats[0][1], font_stats)

        draw_base.text((14 * SPACING + image_skin.width + max(length_stats_left, 80), 8 * SPACING), stats[1][0],
                       (192, 192, 192), font_stats_header)
        draw_base.text((14 * SPACING + image_skin.width + max(length_stats_left, 80), 10 * SPACING), stats[1][1],
                       (77, 189, 138), font_stats)

        animated = False
        frames = []
        for cosmetic in player_cosmetics:
            if cosmetic.type == CosmeticsType.Title:
                effect = cosmetic.color
                animated = effect.type != 'static'

                if animated:
                    for color in effect:
                        frame = image_base.copy()

                        image_ribbon = await self.render_ribbon(str(cosmetic), cosmetic.bold, color)
                        frame.paste(image_ribbon, (image_base.width - 175, SPACING), mask=image_ribbon)
                        frames.append(frame)
                else:
                    image_ribbon = await self.render_ribbon(str(cosmetic), cosmetic.bold, effect[0])
                    image_base.paste(image_ribbon, (image_base.width - 175, SPACING), mask=image_ribbon)

        if animated:
            return Render(*frames)

        return Render(image_base)


class RankCard(PlayerCard):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, 'images/prison.png')

    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str]]:
        return [
            ('RANK', (await player_info.stats_prison).rank),
            ('BLOCKS MINED', get_number_representation((await player_info.stats_prison).blocks)),
        ]


class InfamyCard(PlayerCard):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, 'images/arena.png')

    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str]]:
        return [
            ('INFAMY', str((await player_info.stats_arena).infamy)),
            ('KDA', '{:.2f}'.format((await player_info.stats_arena).kda)),
        ]


class KillsCard(PlayerCard):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, 'images/arena.png')

    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str]]:
        return [
            ('KILLS', str((await player_info.stats_arena).kills)),
            ('ASSISTS', str((await player_info.stats_arena).assists)),
        ]


class KdaCard(PlayerCard):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, 'images/arena.png')

    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str]]:
        return [
            ('KILLS', str((await player_info.stats_arena).kills)),
            ('KDA', '{:.2f}'.format((await player_info.stats_arena).kda)),
        ]


class DeathsCard(PlayerCard):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, 'images/arena.png')

    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str]]:
        return [
            ('DEATHS', str((await player_info.stats_arena).deaths)),
            ('KDA', '{:.2f}'.format((await player_info.stats_arena).kda)),
        ]


class TimeCard(PlayerCard):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, random.choice(['images/prison.png', 'images/arena.png']))  # noqa: S311

    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str]]:
        return [
            ('TIME PLAYED', get_timedelta_representation(await player_info.time_played)),
            ('', ''),
        ]


class WikiCard(PlayerCard):
    def __init__(self, username: str = None, discord_user: nextcord.User = None):
        super().__init__(username, discord_user, random.choice(['images/prison.png', 'images/arena.png']))  # noqa: S311

    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str]]:
        return [
            ('POINTS', str(await player_info.wiki_points)),
            ('', '')
        ]
