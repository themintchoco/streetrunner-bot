from marshmallow import Schema, fields

from bot.api.api import ApiSchema


class StreetRunnerApi(ApiSchema):
    __endpoints__ = ['https://streetrunner.dev/api/']

    def api_get(self):
        return super().api_get(headers={'Authorization': os.environ['API_KEY']})


class Player(StreetRunnerApi):
    __endpoints__ = ['name/{mc_username}/', 'discord/{discord_id}/']


class PlayerInfo(Player):
    username = fields.String()
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


class PlayerStatsTime(Player):
    # TODO: ??
    pass


class PlayerCosmetics(Player):
    __endpoints__ = ['cosmetics/']

    TITLE = fields.String()
    JOIN = fields.String()
    KILL = fields.String()
    PET = fields.String()


class Leaderboard(StreetRunnerApi):
    __endpoints__ = ['leaderboard/']

# TODO: Leaderboards
