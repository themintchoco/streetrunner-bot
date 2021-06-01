class UsernameError(ValueError):
	pass


class DiscordNotLinkedError(UsernameError):
	pass


class NotEnoughDataError(RuntimeError):
	pass