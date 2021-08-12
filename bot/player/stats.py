from enum import Enum


class PlayerStatsType(Enum):
    Prison, Arena = range(2)


class PlayerInfo:
    def __init__(self, player):
        self._player = player
        self._player_info = None
        self._stats_prison = None
        self._stats_arena = None
        self._stats_time = None

    @property
    def uuid(self):
        if not self._player_info:
            self._player_info = self._player.PlayerInfo().preload()

        return self._player_info.data.uuid

    @property
    def username(self):
        if not self._player_info:
            self._player_info = self._player.PlayerInfo().preload()

        return self._player_info.data.name

    @property
    def stats_prison(self):
        if not self._stats_prison:
            self._stats_prison = self._player.PlayerStatsPrison().preload()

        return self._stats_prison.data

    @property
    def stats_arena(self):
        if not self._stats_arena:
            self._stats_arena = self._player.PlayerStatsArena().preload()

        return self._stats_arena.data

    @property
    def time_played(self):
        if not self._stats_arena:
            self._stats_arena = self._player.PlayerStatsTime().preload()

        return self._stats_arena.data.value
