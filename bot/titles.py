import inspect
import sys
from abc import ABC

from colour import Color

from bot.card import ColorEffect, ColorEffectBreathe, Cosmetics, CosmeticsType


class Title(Cosmetics, ABC):

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
        return self.__str__


def from_known_string(string: str) -> Title:
    return next(x for x in Title.__subclasses__() if lambda y: y.id == string)()


class Fiery(Title):
    @property
    def __str__(self) -> str:
        return "FIERY"

    bold = False
    color = ColorEffect('#fc5454')


class FieryBold(Title):
    @property
    def __str__(self) -> str:
        return "FIERY"

    bold = True
    color = ColorEffect('#fc5454')
    id = "FIERY_BOLD"


class Undefeated(Title):
    @property
    def __str__(self) -> str:
        return "UNDEFEATED"

    bold = True
    color = ColorEffect('#fc54fc')


class Supreme(Title):
    @property
    def __str__(self) -> str:
        return "SUPREME"

    bold = True
    color = ColorEffect('#fca800')


class Drake(Title):
    @property
    def __str__(self) -> str:
        return "DRAKE"

    bold = False
    color = ColorEffect('#a80000')


class Champion(Title):
    @property
    def __str__(self) -> str:
        return "CHAMPION"

    bold = True
    color = ColorEffectBreathe(Color('#fc5454'), Color('#fc8e74'), inhale_rate=1.8, exhale_rate=1.2, duration=60)
