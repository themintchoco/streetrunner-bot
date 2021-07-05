from enum import Enum

class CosmeticsType(Enum):
    Title, Pet = range(2)


class Cosmetics:
    def __init__(self, **kwargs):
        self.type = kwargs['type']