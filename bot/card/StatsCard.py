import random
from abc import ABC
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from bot.api_compatability_layer import get_player_cosmetics, get_player_info
from bot.card.PlayerCard import PlayerCard
from bot.card.PlayerModel import PlayerModel
from bot.card.Render import Render
from bot.card.Ribbon import Ribbon
from bot.card.card import FONT_BLACK, FONT_BOLD, FONT_LIGHT, SPACING
from bot.cosmetics.cosmetics import CosmeticsType
from bot.player.stats import PlayerInfo, PlayerStatsType
from helpers.utilities import get_number_representation, get_timedelta_representation

STATS_CARD_WIDTH = 640
STATS_CARD_HEIGHT = 220

STATS_CARD_BACKGROUND = {
    PlayerStatsType.Prison: 'images/prison.jpg',
    PlayerStatsType.Arena: 'images/arena.jpg'
}


class StatsCard(PlayerCard):
    _background = random.choice(list(STATS_CARD_BACKGROUND.values()))

    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str]]:
        raise NotImplementedError()

    async def render(self) -> Render:
        player_info = await get_player_info(username=self._username, discord_user=self._discord_user)
        player_cosmetics = await get_player_cosmetics(username=self._username, discord_user=self._discord_user)
        image_skin = (await PlayerModel(await player_info.uuid, 6).render()).image
        stats = await self.get_stats(player_info)

        image_base = Image.new('RGBA', (STATS_CARD_WIDTH, STATS_CARD_HEIGHT), color=(0, 0, 0, 0))
        draw_base = ImageDraw.Draw(image_base)

        font_username = ImageFont.truetype(FONT_BOLD, 36)
        font_stats_header = ImageFont.truetype(FONT_LIGHT, 18)
        font_stats = ImageFont.truetype(FONT_BLACK, 54)

        length_name = draw_base.textlength(await player_info.username, font_username)

        width_required = 12 * SPACING + image_skin.width + length_name
        if CosmeticsType.Title in player_cosmetics:
            width_required += 135

        if width_required > image_base.width:
            image_base = Image.new('RGBA', (int(width_required), STATS_CARD_HEIGHT), color=(0, 0, 0, 0))
            draw_base = ImageDraw.Draw(image_base)

        image_background = image_base.copy()
        image_background.paste(Image.open(self._background))

        image_mask = image_base.copy()
        draw_mask = ImageDraw.Draw(image_mask)
        draw_mask.ellipse(
            (-STATS_CARD_HEIGHT // 2 - 8 * SPACING, -8 * SPACING, STATS_CARD_HEIGHT // 2 + 8 * SPACING,
             STATS_CARD_HEIGHT + 8 * SPACING),
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

        image_skin = image_skin.crop((0, 0, image_skin.width, STATS_CARD_HEIGHT - 3 * SPACING))

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

        if title := player_cosmetics.get(CosmeticsType.Title):
            ribbon = await (getattr(title, 'ribbon', Ribbon)(title)).render()

            frames = []
            for image in ribbon.images:
                frame = image_base.copy()
                image = image.rotate(-35, expand=True).crop((0, 30, 164, STATS_CARD_HEIGHT))
                frame.paste(image, (image_base.width - 175, SPACING), mask=image)
                frames.append(frame)

            return Render(*frames)

        return Render(image_base)


class PrisonCard(StatsCard, ABC):
    _background = STATS_CARD_BACKGROUND[PlayerStatsType.Prison]


class ArenaCard(StatsCard, ABC):
    _background = STATS_CARD_BACKGROUND[PlayerStatsType.Arena]


class RankCard(PrisonCard):
    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str, str]]:
        return [
            ('RANK', (await player_info.stats_prison).rank),
            ('BLOCKS MINED', get_number_representation((await player_info.stats_prison).blocks)),
        ]


class InfamyCard(ArenaCard):
    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str, str]]:
        return [
            ('INFAMY', str((await player_info.stats_arena).infamy)),
            ('KDA', '{:.2f}'.format((await player_info.stats_arena).kda)),
        ]


class KillsCard(ArenaCard):
    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str, str]]:
        return [
            ('KILLS', str((await player_info.stats_arena).kills)),
            ('ASSISTS', str((await player_info.stats_arena).assists)),
        ]


class KdaCard(ArenaCard):
    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str, str]]:
        return [
            ('KILLS', str((await player_info.stats_arena).kills)),
            ('KDA', '{:.2f}'.format((await player_info.stats_arena).kda)),
        ]


class DeathsCard(ArenaCard):
    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str, str]]:
        return [
            ('DEATHS', str((await player_info.stats_arena).deaths)),
            ('KDA', '{:.2f}'.format((await player_info.stats_arena).kda)),
        ]


class TimeCard(StatsCard):
    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str, str]]:
        return [
            ('TIME PLAYED', get_timedelta_representation(await player_info.time_played)),
            ('', ''),
        ]


class WikiCard(StatsCard):
    async def get_stats(self, player_info: PlayerInfo) -> List[Tuple[str, str]]:
        return [
            ('POINTS', str(await player_info.wiki_points)),
            ('', '')
        ]
