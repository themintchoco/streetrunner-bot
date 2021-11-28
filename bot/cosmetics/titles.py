from colour import Color

from bot.card import Ribbon
from bot.coloreffect import ColorEffect, ColorEffectBreathe, ColorEffectUnicorn
from bot.cosmetics.cosmetics import Cosmetics, CosmeticsType


class Title(Cosmetics):
    def __init__(self, **kwargs):
        super().__init__(type=CosmeticsType.Title)

    def __str__(self) -> str:
        return self.id

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
    bold = False
    color = ColorEffect('#fc5454')
    id = 'FIERY'


class FieryBold(Title):
    def __str__(self) -> str:
        return 'FIERY'

    bold = True
    color = ColorEffect('#fc5454')
    id = 'FIERY_BOLD'
    role = 906008699473104916


class Undefeated(Title):
    bold = True
    color = ColorEffect('#fc54fc')
    id = 'UNDEFEATED'
    role = 906012867772428298


class Supreme(Title):
    bold = True
    color = ColorEffect('#fca800')
    id = 'SUPREME'
    role = 906013315078164490


class Drake(Title):
    bold = False
    color = ColorEffect('#a80000')
    id = 'DRAKE'


class Champion(Title):
    bold = True
    color = ColorEffectBreathe(Color('#fc5454'), Color('#fc8e74'), inhale_rate=1.8, exhale_rate=1.2, duration=60)
    id = 'CHAMPION'
    role = 906109826118086697


class ChampionS1(Champion):
    id = 'CHAMPION_S1'

    def __str__(self):
        return 'CHAMPION¹'


class ChampionS2(Champion):
    id = 'CHAMPION_S2'

    def __str__(self):
        return 'CHAMPION²'


class Vip(Title):
    bold = True
    color = ColorEffectUnicorn(Color('red'), Color('violet'), Color('red'), duration=60)
    id = 'VIP'


class Wealthy(Title):
    bold = False
    color = ColorEffect('#fecd60')
    id = 'WEALTHY'


class WealthyBold(Title):
    def __str__(self) -> str:
        return 'WEALTHY'

    bold = True
    color = ColorEffect('#fecd60')
    id = 'WEALTHY_BOLD'
    role = 906013562403717141


class Exalted(Title):
    bold = True
    font = ColorEffect('black', alpha=0.8)
    color = ColorEffect('#bfff00', duration=30)
    shine = ColorEffect('#00ffff')
    width = 50
    fade_width = 50
    ribbon = Ribbon.RibbonWave
    id = 'EXALTED'
    role = 914038102182465617


known_titles = {x.id: x() for x in Title.known()}


def from_known_string(string: str) -> Title:
    return known_titles[string]
