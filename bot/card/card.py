import asyncio

SPACING = 12

FONT_BLACK = 'fonts/Roboto-Black.ttf'
FONT_BOLD = 'fonts/Roboto-Bold.ttf'
FONT_REGULAR = 'fonts/Roboto-Regular.ttf'
FONT_LIGHT = 'fonts/Roboto-Light.ttf'


async def main():
    import os
    from bot.config import bot

    ready = False

    @bot.event
    async def on_ready():
        nonlocal ready
        if ready:
            return

        ready = True

        from helpers.utilities import resolve_id
        from bot.card.XPLevelUp import XPLevelUp
        (await XPLevelUp(discord_user=resolve_id(244801669043453953),
                         level_before=12, level_after=69).render()).image.show()

        await bot.close()

    await bot.start(os.environ['TOKEN'])


if __name__ == '__main__':
    asyncio.run(main())
