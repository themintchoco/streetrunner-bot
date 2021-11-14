from enum import Enum

import math
from PIL import Image, ImageDraw, ImageFont

from bot.api.StreetRunnerApi.Player import Player
from bot.card.PlayerCard import PlayerCard
from bot.card.PlayerModel import PlayerModel
from bot.card.Render import Render
from bot.card.card import FONT_MC_REGULAR, SPACING
from bot.player.privacy import Privacy
from helpers.utilities import get_number_representation

BALANCE_WIDTH = 480
BALANCE_ICON_WIDTH = 32
BALANCE_RING_RADIUS = 100
BALANCE_RING_WIDTH = 5


class BalanceType(Enum):
    MONEY = 'images/money.png'
    TOKEN = 'images/token.png'
    CREDIT = 'images/credit.png'
    MYSTERIOUS_ESSENCE = 'images/me.png'


class BalanceCard(PlayerCard):
    async def render(self) -> Render:
        self._font = ImageFont.truetype(FONT_MC_REGULAR, 18)

        player = Player({'mc_username': self._username, 'discord_id': self._discord_user.id})
        balances = []

        for balance in await player.PlayerBalance().data:
            try:
                if ((balance_type := BalanceType[balance.type]) in [BalanceType.TOKEN] and
                        not (await player.PlayerPrivacy().data).value & Privacy.balance):
                    continue
            except KeyError:
                continue

            balances.append((balance_type, balance.balance))

        image_base = Image.new('RGBA', (BALANCE_WIDTH, 2 * (BALANCE_RING_RADIUS + BALANCE_ICON_WIDTH + SPACING)),
                               color=(0, 0, 0, 0))
        draw_base = ImageDraw.Draw(image_base)

        draw_base.ellipse((image_base.width // 2 - BALANCE_RING_RADIUS,
                           image_base.height // 2 - BALANCE_RING_RADIUS,
                           image_base.width // 2 + BALANCE_RING_RADIUS,
                           image_base.height // 2 + BALANCE_RING_RADIUS),
                          (0, 0, 0, 0), (127, 127, 127, 143), BALANCE_RING_WIDTH)

        image_model = (await PlayerModel((await player.PlayerInfo().data).uuid, 3).render()).image
        image_base.paste(image_model, ((image_base.width - image_model.width) // 2,
                                       (image_base.height - image_model.height) // 2),
                         mask=image_model)

        angle_sector = 2 * math.pi / len(balances)
        angle = angle_sector / 4
        for balance_type, value in balances:
            direction = (math.sin(angle), -math.cos(angle))
            x = int(direction[0] * BALANCE_RING_RADIUS + image_base.width // 2)
            y = int(direction[1] * BALANCE_RING_RADIUS + image_base.height // 2)

            image_icon = Image.open(balance_type.value).resize((BALANCE_ICON_WIDTH, BALANCE_ICON_WIDTH), Image.NEAREST)
            image_base.paste(image_icon, (x - BALANCE_ICON_WIDTH // 2, y - BALANCE_ICON_WIDTH // 2), mask=image_icon)

            x0, y0, x1, y1 = draw_base.textbbox((x + direction[0] * BALANCE_ICON_WIDTH,
                                                 y + direction[1] * BALANCE_ICON_WIDTH),
                                                get_number_representation(value),
                                                self._font, anchor='rm' if direction[0] < 0 else 'lm')
            draw_base.rectangle((x0 - 6, y0 - 8, x1 + 6, y1 + 8), (27, 12, 27, 248), (0, 0, 0, 0), 0)
            draw_base.rectangle((x0 - 8, y0 - 6, x1 + 8, y1 + 6), (27, 12, 27, 248), (0, 0, 0, 0), 0)
            draw_base.rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), (27, 12, 27, 248), (42, 8, 92, 255), 2)

            draw_base.text((x + direction[0] * BALANCE_ICON_WIDTH,
                            y + direction[1] * BALANCE_ICON_WIDTH),
                           get_number_representation(value),
                           (255, 255, 255), self._font, anchor='rm' if direction[0] < 0 else 'lm')

            angle += angle_sector

        return Render(image_base)
