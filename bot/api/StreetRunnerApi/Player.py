from marshmallow import fields
from marshmallow import post_load

from bot.api.StreetRunnerApi.StreetRunnerApi import StreetRunnerApi


class Player(StreetRunnerApi):
    __endpoints__ = ['name/{mc_username}/', 'discord/{discord_id}/', 'uuid/{uuid}/']


class PlayerInfo(Player):
    name = fields.String()
    uuid = fields.String()
    discord = fields.String(allow_none=True)


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
