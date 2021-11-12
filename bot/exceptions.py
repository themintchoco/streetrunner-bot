from aiohttp import ClientResponseError


class UsernameError(ValueError):
    def __init__(self, username=None, details={}):
        details.setdefault('message', 'The username provided is invalid')
        super().__init__(details)


class DiscordNotLinkedError(UsernameError):
    def __init__(self, discord_id, details={}):
        details.setdefault('message', f'<@{discord_id}> is not linked to StreetRunner. '
                                      'Linking can be done by using the /discord command in-game. ')
        super().__init__(details=details)


class NotEnoughDataError(RuntimeError):
    pass


APIError = ClientResponseError