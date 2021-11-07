class UsernameError(ValueError):
    def __init__(self, username=None):
        super().__init__('The username provided is invalid')


class DiscordNotLinkedError(UsernameError):
    def __init__(self, discord_id):
        super().__init__(f'<@{discord_id}> is not linked to StreetRunner. '
                         'Linking can be done by using the /discord command in-game. ')


class NotEnoughDataError(RuntimeError):
    pass


class APIError(RuntimeError):
    pass
