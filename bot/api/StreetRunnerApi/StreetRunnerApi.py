import os

from bot.api.api import ApiSchema


class StreetRunnerApi(ApiSchema):
    __endpoints__ = ['https://streetrunner.gg/api/']

    def api_get(self):
        return super().api_get(headers={'Authorization': os.environ['API_KEY']})
