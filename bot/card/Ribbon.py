import math

from PIL import Image, ImageDraw, ImageFont

from bot.card.Render import Render, Renderable
from bot.card.card import FONT_BLACK, FONT_REGULAR
from bot.coloreffect import ColorEffect

RIBBON_WIDTH = 215
RIBBON_HEIGHT = 35


class Ribbon(Renderable):
    def __init__(self, title):
        self._text = str(title)
        self._color = title.color
        self._bold = getattr(title, 'bold', False)
        self._font = getattr(title, 'font', ColorEffect('white'))

    async def render_background(self, n) -> Image:
        image_background = Image.new('RGBA', (RIBBON_WIDTH, RIBBON_HEIGHT), color=self._color[n])
        return image_background

    async def render_foreground(self, background, n):
        image_foreground = Image.new('RGBA', background.size, (0, 0, 0, 0))
        draw_foreground = ImageDraw.Draw(image_foreground)

        font_ribbon = ImageFont.truetype(FONT_BLACK if self._bold else FONT_REGULAR, 18)
        draw_foreground.text((image_foreground.width // 2, image_foreground.height // 2),
                             self._text, self._font[n], font_ribbon, anchor='mm')
        return image_foreground

    async def render(self) -> Render:
        frames = []

        for i in range(self._color.duration):
            image_background = await self.render_background(i)
            image_foreground = await self.render_foreground(image_background, i)
            frames.append(Image.alpha_composite(image_background, image_foreground))

        return Render(*frames)


class RibbonShine(Ribbon):
    def __init__(self, title):
        super().__init__(title)
        self._shine = title.shine
        self._width = getattr(title, 'width', 104)
        self._angle = getattr(title, 'angle', -math.pi / 6)

    async def render_background(self, n) -> Image:
        image_background = await super().render_background(n)

        image_shine = Image.new('RGBA', (int(abs(math.sin(self._angle)) * self._width),
                                         int(image_background.height / abs(math.sin(self._angle)) + abs(math.cos(self._angle)) * self._width)),
                                color=self._shine[n % self._shine.duration])
        image_shine = image_shine.rotate(math.degrees(self._angle), expand=True)
        image_background.alpha_composite(image_shine,
                                         (int(n / self._color.duration * (image_background.width + 2 * image_shine.width) - image_shine.width), -(image_shine.height - image_background.height) // 2))

        return image_background
