import functools
from enum import Enum


class CosmeticsType(Enum):
    Title, Pet = range(2)


class Cosmetics:
    def __init__(self, **kwargs):
        self.type = kwargs['type']

    @classmethod
    def known(cls):
        subclasses = set()
        work = [cls]

        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses:
                    subclasses.add(child)
                    work.append(child)

        return subclasses

    @classmethod
    def roles(cls):
        return [role for x in [cls, *cls.known()] if (role := getattr(x, 'role', None))]
