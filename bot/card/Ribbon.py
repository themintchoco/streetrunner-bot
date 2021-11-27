import asyncio
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
        image_background = Image.new('RGBA', (RIBBON_WIDTH, RIBBON_HEIGHT), color=self._color.rgba(n))
        return image_background

    async def render_foreground(self, background, n):
        image_foreground = Image.new('RGBA', background.size, (0, 0, 0, 0))
        draw_foreground = ImageDraw.Draw(image_foreground)

        font_ribbon = ImageFont.truetype(FONT_BLACK if self._bold else FONT_REGULAR, 18)
        draw_foreground.text((image_foreground.width // 2, image_foreground.height // 2),
                             self._text, self._font.rgba(n), font_ribbon, anchor='mm')
        return image_foreground

    async def render(self) -> Render:
        a = zip(backgrounds := await asyncio.gather(*(self.render_background(i) for i in range(self._color.duration))),
            await asyncio.gather(*(self.render_foreground(backgrounds[i], i) for i in range(self._color.duration))))
        frames = [Image.alpha_composite(image_background, image_foreground) for image_background, image_foreground in a]
        return Render(*frames)


class RibbonShine(Ribbon):
    def __init__(self, title):
        super().__init__(title)
        self._shine = title.shine
        self._width = getattr(title, 'width', 100)
        self._angle = getattr(title, 'angle', math.pi / 6)

    async def render_shine(self, background, n):
        return Image.new('RGBA', (self._width, background.height),
                         color=self._shine.rgba(n % self._shine.duration))

    async def render_background(self, n) -> Image:
        image_background = await super().render_background(n)
        image_shine = await self.render_shine(image_background, n)

        offset = int(math.tan(abs(self._angle)) * image_shine.height)
        image_overlay = Image.new('RGBA', (image_shine.width + offset, image_shine.height), (0, 0, 0, 0))
        image_overlay.paste(image_shine, (0 if self._angle < 0 else offset, 0))
        image_overlay = image_overlay.transform(image_overlay.size, Image.AFFINE, (1, self._angle, 0, 0, 1, 0))
        image_background.alpha_composite(image_overlay,
                                         (int(n / self._color.duration * (image_background.width + 2 * image_overlay.width) - image_overlay.width), 0))

        return image_background


class RibbonWave(RibbonShine):
    def __init__(self, title):
        super().__init__(title)
        self._fade = getattr(title, 'fade_width', self._width // 2)

    async def render_shine(self, background, n):
        color = self._shine.rgba(n % self._shine.duration)

        image_shine = Image.new('RGBA', (self._width + 2 * self._fade, background.height), color=color)
        draw_shine = ImageDraw.Draw(image_shine)

        for i in range(self._fade):
            c = (color[0], color[1], color[2], int(color[3] * i / self._fade))
            x1, x2 = 2 * self._fade + self._width - i, i
            draw_shine.line([(x1, 0), (x1, image_shine.height)], c, width=1)
            draw_shine.line([(x2, 0), (x2, image_shine.height)], c, width=1)

        return image_shine
