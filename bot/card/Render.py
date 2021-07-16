from io import BytesIO

from helpers.pil_transparent_gifs import save_transparent_gif


class Render:
    def __init__(self, *images: Image.Image, **attributes):
        self._images = images
        self._attributes = attributes

    def __getattr__(self, attr: str):
        try:
            return self._attributes[attr]
        except KeyError:
            raise AttributeError()

    @property
    def image(self) -> Image.Image:
        return self._images[0]

    @property
    def multi_frame(self) -> bool:
        return len(self._images) > 1

    def file(self, *args, **kwargs) -> BytesIO:
        fp = BytesIO()
        self.image.save(fp, *args, **kwargs)
        fp.seek(0)

        return fp

    def file_animated(self, *args, **kwargs) -> BytesIO:
        fp = BytesIO()
        save_transparent_gif(self._images, 1, fp)
        # self.image.save(fp, save_all=True, append_images=self._images[1:], *args, **kwargs)
        fp.seek(0)

        return fp


class Renderable:
    async def render(self) -> Render:
        raise NotImplementedError()