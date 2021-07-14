from PIL import Image

from bot.api import get_skin
from bot.card.card import Render, Renderable


class PlayerModel(Renderable):
    def __init__(self, uuid: str, scale: int):
        self._uuid = uuid
        self._scale = scale

    async def render(self) -> Render:
        image_render = Image.new('RGBA', (20 * self._scale, 45 * self._scale), (0, 0, 0, 0))

        skin_data = await get_skin(self._uuid)
        skin = skin_data['skin']
        slim = skin_data['slim']

        image_skin = Image.open(skin)
        skin_is_old = image_skin.height == 32
        arm_width = 3 if slim else 4

        head_top = image_skin.crop((8, 0, 16, 8)).resize((8 * self._scale, 8 * self._scale), Image.NEAREST)
        head_front = image_skin.crop((8, 8, 16, 16)).resize((8 * self._scale, 8 * self._scale), Image.NEAREST)
        head_right = image_skin.crop((0, 8, 8, 16)).resize((8 * self._scale, 8 * self._scale), Image.NEAREST)

        arm_right_top = image_skin.crop((44, 16, 44 + arm_width, 20)).resize((arm_width * self._scale, 4 * self._scale),
                                                                             Image.NEAREST)
        arm_right_front = image_skin.crop((44, 20, 44 + arm_width, 32)).resize(
            (arm_width * self._scale, 12 * self._scale), Image.NEAREST)
        arm_right_side = image_skin.crop((40, 20, 44, 32)).resize((4 * self._scale, 12 * self._scale), Image.NEAREST)

        arm_left_top = arm_right_top.transpose(method=Image.FLIP_LEFT_RIGHT) if skin_is_old else image_skin.crop(
            (36, 48, 36 + arm_width, 52)).resize((arm_width * self._scale, 4 * self._scale), Image.NEAREST)
        arm_left_front = arm_right_front.transpose(method=Image.FLIP_LEFT_RIGHT) if skin_is_old else image_skin.crop(
            (36, 52, 36 + arm_width, 64)).resize((arm_width * self._scale, 12 * self._scale), Image.NEAREST)

        leg_right_front = image_skin.crop((4, 20, 8, 32)).resize((4 * self._scale, 12 * self._scale), Image.NEAREST)
        leg_right_side = image_skin.crop((0, 20, 4, 32)).resize((4 * self._scale, 12 * self._scale), Image.NEAREST)

        leg_left_front = leg_right_front.transpose(method=Image.FLIP_LEFT_RIGHT) if skin_is_old else image_skin.crop(
            (20, 52, 24, 64)).resize((4 * self._scale, 12 * self._scale), Image.NEAREST)

        body_front = image_skin.crop((20, 20, 28, 32)).resize((8 * self._scale, 12 * self._scale), Image.NEAREST)

        if image_skin.crop((32, 0, 64, 32)).getextrema()[3][0] < 255:
            head_top.alpha_composite(
                image_skin.crop((40, 0, 48, 8)).resize((8 * self._scale, 8 * self._scale), Image.NEAREST))
            head_front.alpha_composite(
                image_skin.crop((40, 8, 48, 16)).resize((8 * self._scale, 8 * self._scale), Image.NEAREST))
            head_right.alpha_composite(
                image_skin.crop((32, 8, 40, 16)).resize((8 * self._scale, 8 * self._scale), Image.NEAREST))

        if not skin_is_old:
            if image_skin.crop((16, 32, 48, 48)).getextrema()[3][0] < 255:
                body_front.alpha_composite(
                    image_skin.crop((20, 36, 28, 48)).resize((8 * self._scale, 12 * self._scale), Image.NEAREST))

            if image_skin.crop((48, 48, 64, 64)).getextrema()[3][0] < 255:
                arm_right_top.alpha_composite(
                    image_skin.crop((44, 32, 44 + arm_width, 36)).resize((arm_width * self._scale, 4 * self._scale),
                                                                         Image.NEAREST))
                arm_right_front.alpha_composite(
                    image_skin.crop((44, 36, 44 + arm_width, 48)).resize((arm_width * self._scale, 12 * self._scale),
                                                                         Image.NEAREST))
                arm_right_side.alpha_composite(
                    image_skin.crop((40, 36, 44, 48)).resize((4 * self._scale, 12 * self._scale), Image.NEAREST))

            if image_skin.crop((40, 32, 56, 48)).getextrema()[3][0] < 255:
                arm_left_top.alpha_composite(
                    image_skin.crop((52, 48, 52 + arm_width, 52)).resize((arm_width * self._scale, 4 * self._scale),
                                                                         Image.NEAREST))
                arm_left_front.alpha_composite(
                    image_skin.crop((52, 52, 52 + arm_width, 64)).resize((arm_width * self._scale, 12 * self._scale),
                                                                         Image.NEAREST))

            if image_skin.crop((0, 32, 16, 48)).getextrema()[3][0] < 255:
                leg_right_front.alpha_composite(
                    image_skin.crop((4, 36, 8, 48)).resize((4 * self._scale, 12 * self._scale), Image.NEAREST))
                leg_right_side.alpha_composite(
                    image_skin.crop((0, 36, 4, 48)).resize((4 * self._scale, 12 * self._scale), Image.NEAREST))

            if image_skin.crop((0, 48, 16, 64)).getextrema()[3][0] < 255:
                leg_left_front.alpha_composite(
                    image_skin.crop((4, 52, 8, 64)).resize((4 * self._scale, 12 * self._scale), Image.NEAREST))

        front = Image.new('RGBA', (16 * self._scale, 24 * self._scale), (0, 0, 0, 0))
        front.alpha_composite(arm_right_front, ((4 - arm_width) * self._scale, 0))
        front.alpha_composite(arm_left_front, (12 * self._scale, 0))
        front.alpha_composite(body_front, (4 * self._scale, 0))
        front.alpha_composite(leg_right_front, (4 * self._scale, 12 * self._scale))
        front.alpha_composite(leg_left_front, (8 * self._scale, 12 * self._scale))

        x_offset = 2 * self._scale
        z_offset = 3 * self._scale

        x = x_offset + self._scale * 2
        y = self._scale * -arm_width
        z = z_offset + self._scale * 8
        render_top = Image.new('RGBA', (image_render.width * 4, image_render.height * 4), (0, 0, 0, 0))
        render_top.paste(arm_right_top, (
            y - z + (render_top.width - image_render.width) // 2,
            x + z + (render_top.height - image_render.height) // 2))

        y = self._scale * 8
        render_top.alpha_composite(arm_left_top, (
            y - z + (render_top.width - image_render.width) // 2,
            x + z + (render_top.height - image_render.height) // 2))

        x = x_offset
        y = 0
        z = z_offset
        render_top.alpha_composite(head_top, (
            y - z + (render_top.width - image_render.width) // 2,
            x + z + (render_top.height - image_render.height) // 2))

        render_top = render_top.transform((render_top.width * 2, render_top.height), Image.AFFINE,
                                          (0.5, -45 / 52, 0, 0.5, 45 / 52, 0))

        x = x_offset + self._scale * 2
        y = 0
        z = z_offset + self._scale * 20
        render_right = Image.new('RGBA', (image_render.width, image_render.height), (0, 0, 0, 0))
        render_right.paste(leg_right_side, (x + y, z - y))

        x = x_offset + self._scale * 2
        y = self._scale * -arm_width
        z = z_offset + self._scale * 8
        render_right.alpha_composite(arm_right_side, (x + y, z - y))

        x = x_offset
        y = 0
        z = z_offset
        render_right_head = Image.new('RGBA', (image_render.width, image_render.height), (0, 0, 0, 0))
        render_right_head.alpha_composite(head_right, (x + y, z - y))

        render_right = render_right.transform((image_render.width, image_render.height), Image.AFFINE,
                                              (1, 0, 0, -0.5, 45 / 52, 0))
        render_right_head = render_right_head.transform((image_render.width, image_render.height), Image.AFFINE,
                                                        (1, 0, 0, -0.5, 45 / 52, 0))

        x = x_offset + self._scale * 2
        y = 0
        z = z_offset + self._scale * 12
        render_front = Image.new('RGBA', (image_render.width, image_render.height), (0, 0, 0, 0))
        render_front.paste(front, (y + x, x + z))

        x = x_offset + 8 * self._scale
        y = 0
        z = z_offset
        render_front.alpha_composite(head_front, (y + x, x + z))

        render_front = render_front.transform((image_render.width, image_render.height), Image.AFFINE,
                                              (1, 0, 0, 0.5, 45 / 52, -0.5))

        image_render.paste(render_top, (round(-97.5 * self._scale + 1 / 6), round(-21.65 * self._scale + 0.254)))
        image_render.alpha_composite(render_right)
        image_render.alpha_composite(render_front)
        image_render.alpha_composite(render_right_head)

        return Render(image_render)
