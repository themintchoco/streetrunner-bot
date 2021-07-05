from abc import ABC

from bot.cosmetics.cosmetics import Cosmetics, CosmeticsType


class Pet(Cosmetics, ABC):
    def __init__(self, **kwargs):
        super().__init__(type=CosmeticsType.Pet)
