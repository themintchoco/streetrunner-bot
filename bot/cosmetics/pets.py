from bot.cosmetics.cosmetics import Cosmetics, CosmeticsType


class Pet(Cosmetics):
    def __init__(self, **kwargs):
        super().__init__(type=CosmeticsType.Pet)


class BB8(Pet):
    id = 'BB8'
    role = 906112174706028554


class Boxer(Pet):
    id = 'BOXER'
    role = 906009084791246888


class Duck(Pet):
    id = 'DUCK'
    role = 906110346215948288


class Frog(Pet):
    id = 'FROG'
    role = 906110637397131284


def inheritors(klass):
    subclasses = set()
    work = [klass]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses


known_pets = {x.id: x() for x in Pet.known()}


def from_known_string(string: str) -> Pet:
    return known_pets[string]
