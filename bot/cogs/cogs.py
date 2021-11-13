from enum import Enum

from bot.exceptions import PrivacyError
from bot.player.privacy import Privacy


class PlayerRespondType(Enum):
    Source, DM = range(2)


class PlayerRespondMixin:
    async def respond(self, ctx, player, privacy: Privacy = 0, *args, **kwargs) -> bool:
        async with ctx.typing():
            target = ctx

            if (await player.PlayerPrivacy().data).value & privacy:
                player_info = await player.PlayerInfo().data

                if (target := self.bot.get_user(player_info.discord)) != ctx.author:
                    raise PrivacyError(player_info)

        await target.send(*args, **kwargs)
        return PlayerRespondType.Source if target == ctx else PlayerRespondType.DM
