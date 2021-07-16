from enum import Enum


class LeaderboardType(Enum):
    Rank, Kda, Kills, Blocks, Infamy, Deaths, Time = range(7)