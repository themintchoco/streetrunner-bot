import datetime

from bot.config import bot


class SingletonBase:
    def __new__(cls, *args, **kwargs):
        if not 'instance' in cls.__dict__:
            cls.instance = super().__new__(cls, *args, **kwargs)
        return cls.instance


def resolve_id(discord_id: int):
    return bot.get_user(discord_id)


def get_number_representation(number: int) -> str:
    magnitude = (len(str(number)) - 1) // 3
    return f'{(number / (10 ** (magnitude * 3))):.3g}{" KMBTPEZY"[magnitude] if magnitude > 0 else ""}'


def get_timedelta_representation(td: datetime.timedelta, *, only_hours=False) -> str:
    if only_hours:
        hours = td.total_seconds() / 3600
        repr = f'{hours:.2f}h' if hours else ''
    else:
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        repr = (f'{int(hours)}h ' if hours else '') + (f'{int(minutes)}m ' if minutes else '')

    return repr if repr else 'Not played yet'
