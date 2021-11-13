import os

from bot.api.api import ApiSchema


class StreetRunnerApi(ApiSchema):
    __endpoints__ = ['https://streetrunner.gg/api/']

    def api_get(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).setdefault('Authorization', os.environ['API_KEY'])
        kwargs.setdefault('ssl', False)
        return super().api_get(*args, **kwargs)

    def api_post(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).setdefault('Authorization', os.environ['API_KEY'])
        kwargs.setdefault('ssl', False)
        return super().api_post(*args, **kwargs)
