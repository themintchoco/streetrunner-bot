from PIL import Image

from bot.api_compatability_layer import get_skin
from bot.card.Render import Render, Renderable


class Avatar(Renderable):
    def __init__(self, uuid, scale=10):
        self._uuid = uuid
        self._scale = scale

    async def render(self) -> Render:
        image_skin = Image.open((await get_skin(self._uuid))['skin'])

        head_front = image_skin.crop((8, 8, 16, 16)).resize((8 * self._scale, 8 * self._scale), Image.NEAREST)
        if image_skin.crop((32, 0, 64, 32)).getextrema()[3][0] < 255:
            head_front.alpha_composite(
                image_skin.crop((40, 8, 48, 16)).resize((8 * self._scale, 8 * self._scale), Image.NEAREST))

        return Render(head_front)
