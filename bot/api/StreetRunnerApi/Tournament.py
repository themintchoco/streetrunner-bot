import datetime

from marshmallow import fields

from bot.api.StreetRunnerApi.StreetRunnerApi import StreetRunnerApi


class Tournament(StreetRunnerApi):
    __endpoints__ = ['tournament/']


class TournamentData(Tournament):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('many', True)
        super().__init__(*args, **kwargs)

    name = fields.String()
    value = fields.Integer()
    uuid = fields.String()
    kills = fields.Integer()
    deaths = fields.Integer()
    assists = fields.Integer()


class TournamentPosition(Tournament):
    __endpoints__ = ['{uuid}/']

    value = fields.Integer()