from typing import Iterable, Optional, TypeVar

from PIL import Image, ImageDraw

from bot.card.card import SPACING
from bot.card.Render import Render, Renderable
from bot.player.stats import PlayerInfo

T = TypeVar('T')
LEADERBOARD_GENERIC_WIDTH = 580


class GenericLeaderboard(Renderable):
    @property
    async def data(self) -> Iterable[T]:
        raise NotImplementedError()

    @property
    async def target(self) -> Optional[T]:
        return None

    @property
    async def target_position(self) -> int:
        return -1

    @property
    async def fill_separator(self) -> bool:
        return False

    async def render_row(self, ctx, player_info: PlayerInfo) -> Render:
        raise NotImplementedError()

    async def render_separator(self, ctx) -> Render:
        image_dots = Image.new('RGBA', (ctx['ROW_WIDTH'], 30), color=(0, 0, 0, 0))
        radius = 10

        draw_dots = ImageDraw.Draw(image_dots)
        draw_dots.ellipse(
            ((ctx['ROW_WIDTH'] - radius) // 2, (30 - radius) // 2,
             (ctx['ROW_WIDTH'] + radius) // 2,
             (30 + radius) // 2),
            fill=(209, 222, 241, 255))
        draw_dots.ellipse(
            ((ctx['ROW_WIDTH'] - 5 * SPACING - radius) // 2, (30 - radius) // 2,
             (ctx['ROW_WIDTH'] - 5 * SPACING + radius) // 2, (30 + radius) // 2),
            fill=(209, 222, 241, 255))
        draw_dots.ellipse(
            ((ctx['ROW_WIDTH'] + 5 * SPACING - radius) // 2, (30 - radius) // 2,
             (ctx['ROW_WIDTH'] + 5 * SPACING + radius) // 2, (30 + radius) // 2),
            fill=(209, 222, 241, 255))

        return Render(image_dots)

    async def render(self) -> Render:
        async def get_rows():
            rows = []
            for i, entry in enumerate(self._data):
                if self._target_position > 4 and i > 3 or i > 4:
                    break

                rows.append(
                    (await self.render_row({**ctx, 'POSITION': i + 1, 'ROW_HEIGHT': 75 + (2 if i else 4) * SPACING},
                                           entry)).image)

            if self._target_position > 4:
                rows.append(
                    (await self.render_row(
                        {**ctx, 'POSITION': self._target_position + 1, 'ROW_HEIGHT': 75 + 4 * SPACING},
                        self._target)).image)

            return rows

        self._data = await self.data
        self._target = await self.target
        self._target_position = await self.target_position
        self._separator_filled = await self.fill_separator

        ctx = {
            'ROW_WIDTH': LEADERBOARD_GENERIC_WIDTH,
            'ROW_HEIGHT': 75 + 2 * SPACING,
        }

        rows = await get_rows()

        rows_width = max(row.width for row in rows)
        if rows_width > ctx['ROW_WIDTH']:
            ctx['ROW_WIDTH'] = rows_width
            rows = await get_rows()

        rows_height = sum(row.height for row in rows)

        if self._target_position < 5:
            image_base = Image.new('RGBA', (rows_width, rows_height), color=(0, 0, 0, 0))
            draw_base = ImageDraw.Draw(image_base)

            draw_base.rounded_rectangle((0, 0, rows_width, rows_height),
                                        fill=(32, 34, 37, 255), radius=15)
        else:
            render_separator = await self.render_separator({'ROW_WIDTH': rows_width})
            image_separator = render_separator.image
            image_separator_height = getattr(render_separator, 'preferred_height', image_separator.height)

            image_base = Image.new('RGBA', (rows_width, rows_height + image_separator_height),
                                   color=(0, 0, 0, 0))
            draw_base = ImageDraw.Draw(image_base)

            if self._separator_filled:
                draw_base.rounded_rectangle(
                    (0, 0, rows_width, rows_height + image_separator_height),
                    fill=(32, 34, 37, 255), radius=15)
            else:
                draw_base.rounded_rectangle((0, 0, rows_width, rows_height - rows[-1].height),
                                            fill=(32, 34, 37, 255), radius=15)
                draw_base.rounded_rectangle(
                    (0, rows_height - rows[-1].height + image_separator_height, rows_width,
                     rows_height + image_separator_height),
                    fill=(32, 34, 37, 255), radius=15)

            image_base.paste(image_separator, (
                0, rows_height - rows[-1].height - (image_separator.height - image_separator_height) // 2),
                             mask=image_separator)
            image_base.paste(rows[-1], (0, rows_height - rows[-1].height + image_separator_height), mask=rows[-1])
            rows.pop()

        image_highlight = Image.new('RGBA', (rows_width, rows[0].height), color=(23, 24, 26, 255))
        image_base.paste(image_highlight, mask=image_base.crop((0, 0, image_highlight.width, image_highlight.height)))

        current_offset = 0
        for row in rows:
            image_base.paste(row, (0, current_offset), mask=row)
            current_offset += row.height

        return Render(image_base)
