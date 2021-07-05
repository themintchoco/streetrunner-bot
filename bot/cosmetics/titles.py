from abc import ABC

from colour import Color

from bot.coloreffect import ColorEffect, ColorEffectBreathe
from bot.cosmetics.cosmetics import Cosmetics, CosmeticsType


class Title(Cosmetics, ABC):
    def __init__(self, **kwargs):
        super().__init__(type=CosmeticsType.Title)

    @property
    def __str__(self) -> str:
        raise NotImplementedError

    @property
    def bold(self) -> bool:
        raise NotImplementedError

    @property
    def color(self) -> ColorEffect:
        raise NotImplementedError

    @property
    def id(self) -> str:
        raise NotImplementedError


class Fiery(Title):
    @property
    def __str__(self) -> str:
        return 'FIERY'

    bold = False
    color = ColorEffect('#fc5454')
    id = 'FIERY'


class FieryBold(Title):
    @property
    def __str__(self) -> str:
        return 'FIERY'

    bold = True
    color = ColorEffect('#fc5454')
    id = 'FIERY_BOLD'


class Undefeated(Title):
    @property
    def __str__(self) -> str:
        return 'UNDEFEATED'

    bold = True
    color = ColorEffect('#fc54fc')
    id = 'UNDEFEATED'


class Supreme(Title):
    @property
    def __str__(self) -> str:
        return 'SUPREME'

    bold = True
    color = ColorEffect('#fca800')
    id = 'SUPREME'


class Drake(Title):
    @property
    def __str__(self) -> str:
        return 'DRAKE'

    bold = False
    color = ColorEffect('#a80000')
    id = 'DRAKE'


class Champion(Title):
    @property
    def __str__(self) -> str:
        return 'CHAMPION'

    bold = True
    color = ColorEffectBreathe(Color('#fc5454'), Color('#fc8e74'), inhale_rate=1.8, exhale_rate=1.2, duration=60)
    id = 'CHAMPION'


known_titles = {x.id: x for x in Title.__subclasses__()}


def from_known_string(string: str) -> Title:
    return known_titles[string]()
