from enum import Enum


class PlayerStatsType(Enum):
    Prison, Arena = range(2)


class PlayerStats:
    def __init__(self, **kwargs):
        self.type = kwargs['type']


class PlayerStatsPrison(PlayerStats):
    def __init__(self, **kwargs):
        super().__init__(type=PlayerStatsType.Prison)
        self.rank = kwargs['rank']
        self.blocks = kwargs['blocks']


class PlayerStatsArena(PlayerStats):
    def __init__(self, **kwargs):
        super().__init__(type=PlayerStatsType.Arena)
        self.infamy = kwargs['infamy']
        self.kills = kwargs['kills']
        self.deaths = kwargs['deaths']
        self.assists = kwargs['assists']

    @property
    def kda(self) -> float:
        return round((self.kills + self.assists) / max(self.deaths, 1), 2)


class PlayerInfo:
    def __init__(self, uuid, username, **kwargs):
        self.uuid = uuid
        self.username = username
        self.stats_prison = kwargs.get('stats_prison', None)
        self.stats_arena = kwargs.get('stats_arena', None)
        self.time_played = kwargs.get('time_played', None)