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
        self._stats_wiki = None

    @property
    async def uuid(self):
        if not self._player_info:
            self._player_info = await self._player.PlayerInfo().preload()

        return (await self._player_info.data).uuid

    @property
    async def username(self):
        if not self._player_info:
            self._player_info = await self._player.PlayerInfo().preload()

        return (await self._player_info.data).name

    @property
    async def stats_prison(self):
        if not self._stats_prison:
            self._stats_prison = await self._player.PlayerStatsPrison().preload()

        return await self._stats_prison.data

    @property
    async def stats_arena(self):
        if not self._stats_arena:
            self._stats_arena = await self._player.PlayerStatsArena().preload()

        return await self._stats_arena.data

    @property
    async def time_played(self):
        if not self._stats_time:
            self._stats_time = await self._player.PlayerStatsTime().preload()

        return (await self._stats_time.data).value

    @property
    async def wiki_points(self):
        if not self._stats_wiki:
            self._stats_wiki = await self._player.WikiPoints().preload()

        return (await self._stats_wiki.data).value
