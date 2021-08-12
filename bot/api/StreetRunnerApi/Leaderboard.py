import datetime

from marshmallow import fields

from bot.api.StreetRunnerApi.StreetRunnerApi import StreetRunnerApi


class Leaderboard(StreetRunnerApi):
    __endpoints__ = ['leaderboard/']


class LeaderboardData(Leaderboard):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('many', True)
        super().__init__(*args, **kwargs)

    value = fields.String()
    uuid = fields.String()


class LeaderboardBlocks(LeaderboardData):
    __endpoints__ = ['blocks/']

    value = fields.Integer()


class LeaderboardDeaths(LeaderboardData):
    __endpoints__ = ['deaths/']

    value = fields.Integer()


class LeaderboardInfamy(LeaderboardData):
    __endpoints__ = ['infamy/']


class LeaderboardKda(LeaderboardData):
    __endpoints__ = ['kda/']

    value = fields.Float()


class LeaderboardKills(LeaderboardData):
    __endpoints__ = ['kills/']

    value = fields.Integer()


class LeaderboardRank(LeaderboardData):
    __endpoints__ = ['rank/']


class LeaderboardTime(LeaderboardData):
    __endpoints__ = ['time/']

    value = fields.Function(deserialize=lambda value: datetime.timedelta(seconds=float(value)))


class LeaderboardDataPosition(LeaderboardBlocks, LeaderboardDeaths, LeaderboardInfamy, LeaderboardKda,
                              LeaderboardKills, LeaderboardRank, LeaderboardTime):
    __endpoints__ = ['{uuid}/']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('many', False)
        super().__init__(*args, **kwargs)

    value = fields.Integer()
