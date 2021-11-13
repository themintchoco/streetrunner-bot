from marshmallow import fields
from marshmallow import post_load

from bot.api.StreetRunnerApi.StreetRunnerApi import StreetRunnerApi
from bot.exceptions import APIError, UsernameError, DiscordNotLinkedError


class Player(StreetRunnerApi):
    __endpoints__ = ['name/{mc_username}/', 'discord/{discord_id}/', 'uuid/{uuid}/']

    def api_get_404(self):
        if username := self._params.get('mc_username'):
            raise UsernameError(username)
        elif discord_id := self._params.get('discord_id'):
            raise DiscordNotLinkedError(discord_id)


class PlayerInfo(Player):
    name = fields.String()
    uuid = fields.String()
    discord = fields.Integer(allow_none=True)


class PlayerPrivacy(Player):
    __endpoints__ = ['privacy/']

    value = fields.Integer()


class PlayerStatsPrison(Player):
    __endpoints__ = ['prison/']

    rank = fields.String()
    blocks = fields.Integer()


class PlayerStatsArena(Player):
    __endpoints__ = ['arena/']

    infamy = fields.Integer()
    kills = fields.Integer()
    assists = fields.Integer()
    deaths = fields.Integer()

    @post_load
    def calculate_kda(self, data, **kwargs):
        data['kda'] = (data['kills'] + data['assists']) / max(1, data['deaths'])
        return data


class PlayerStatsTime(Player):
    __endpoints__ = ['time/']

    value = fields.TimeDelta()


class PlayerXP(Player):
    __endpoints__ = ['xp/']

    value = fields.Integer()


class PlayerCosmetics(Player):
    __endpoints__ = ['cosmetics/']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('many', True)
        super().__init__(*args, **kwargs)

    type = fields.String()
    name = fields.String()


class WikiPoints(Player):
    __endpoints__ = ['wiki/']

    value = fields.Float()


class PlayerBalance(Player):
    __endpoints__ = ['balance/']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('many', True)
        super().__init__(*args, **kwargs)

    type = fields.String()
    balance = fields.Integer()
