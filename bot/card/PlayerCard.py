from abc import ABC

import nextcord

from bot.card.Render import Renderable
from bot.player.privacy import Privacy


class PlayerCard(Renderable, ABC):
    def __init__(self, username: str = None, discord_user: nextcord.User = None, privacy: Privacy = 0):
        self._username = username
        self._discord_user = discord_user
        self._privacy = privacy
