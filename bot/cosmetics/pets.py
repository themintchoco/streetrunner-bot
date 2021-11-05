from bot.cosmetics.cosmetics import Cosmetics, CosmeticsType


class Pet(Cosmetics):
    def __init__(self, **kwargs):
        super().__init__(type=CosmeticsType.Pet)


class AmongUsRed(Pet):
    id = 'AMONG_US_RED'
    role = 906120900288602132


class AmongUsOrange(Pet):
    id = 'AMONG_US_ORANGE'
    role = 906119510606610482


class AmongUsYellow(Pet):
    id = 'AMONG_US_YELLOW'
    role = 906123863077847081


class AmongUsLime(Pet):
    id = 'AMONG_US_LIME'
    role = 906120569110556692


class AmongUsGreen(Pet):
    id = 'AMONG_US_GREEN'
    role = 906124042052984842


class AmongUsCyan(Pet):
    id = 'AMONG_US_CYAN'
    role = 906120397987131442


class AmongUsBlue(Pet):
    id = 'AMONG_US_BLUE'
    role = 906124301504229406


class AmongUsPurple(Pet):
    id = 'AMONG_US_PURPLE'
    role = 906120734546481183


class AmongUsPink(Pet):
    id = 'AMONG_US_PINK'
    role = 906119152891219988


class AmongUsBrown(Pet):
    id = 'AMONG_US_BROWN'
    role = 906124193169543178


class AmongUsWhite(Pet):
    id = 'AMONG_US_WHITE'
    role = 906120273399517225


class AmongUsGray(Pet):
    id = 'AMONG_US_GRAY'
    role = 906120214050140180


class AmongUsBlack(Pet):
    id = 'AMONG_US_BLACK'
    role = 906119374451142718


class BB8(Pet):
    id = 'MP8'
    role = 906112174706028554


class Batman(Pet):
    id = 'BATMAN'
    role = 906118162502795294


class Boxer(Pet):
    id = 'BOXER'
    role = 906009084791246888


class Clownfish(Pet):
    id = 'CLOWNFISH'
    role = 906118411187273749


class Duck(Pet):
    id = 'DUCK'
    role = 906110346215948288


class Frog(Pet):
    id = 'FROG'
    role = 906110637397131284


class FlamePrincess(Pet):
    id = 'FLAME_PRINCESS'
    role = 906117350175178762


class Ghost(Pet):
    id = 'GHOST'
    role = 906125027961872404


class GhostMultiple(Pet):
    id = 'GHOST_MULTIPLE'
    role = 906125143191982102


class GhostSwarm(Pet):
    id = 'GHOST_SWARM'
    role = 906126312039661578


class Panda(Pet):
    id = 'PANDA'
    role = 906115542149115914


class Penguin(Pet):
    id = 'PENGUIN'
    role = 906116898423439360


class Pikachu(Pet):
    id = 'PIKACHU'
    role = 906117875121668117


class Pug(Pet):
    id = 'PUG'
    role = 906009084791246888


class Spiderman(Pet):
    id = 'SPIDERMAN'
    role = 906118589290012672


class SteveCreeper(Pet):
    id = 'STEVE_CREEPER'
    role = 906130204978712596


class SteveSkeleton(Pet):
    id = 'STEVE_SKELETON'
    role = 906129742288269383


class SteveZombie(Pet):
    id = 'STEVE_ZOMBIE'
    role = 906130632629956628


class Turtle(Pet):
    id = 'TURTLE'
    role = 906116479920005130


class Witch(Pet):
    id = 'WITCH'
    role = 906127518921277481


known_pets = {x.id: x() for x in Pet.known()}


def from_known_string(string: str) -> Pet:
    return known_pets[string]
