from marshmallow import fields

from bot.api.StreetRunnerApi.StreetRunnerApi import StreetRunnerApi


class Player(StreetRunnerApi):
    __endpoints__ = ['name/{mc_username}/', 'discord/{discord_id}/', 'uuid/{uuid}/']


class PlayerInfo(Player):
    name = fields.String()
    uuid = fields.String()


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

    kda = fields.Function(lambda obj: (obj.kills + obj.assists) / max(1, obj.deaths))


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
