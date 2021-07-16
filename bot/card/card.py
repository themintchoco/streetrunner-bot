SPACING = 12

FONT_BLACK = 'fonts/Roboto-Black.ttf'
FONT_BOLD = 'fonts/Roboto-Bold.ttf'
FONT_REGULAR = 'fonts/Roboto-Regular.ttf'
FONT_LIGHT = 'fonts/Roboto-Light.ttf'


async def main():
    from bot.card.TimeLeaderboard import TimeLeaderboard
    (await TimeLeaderboard(username='threeleaves').render()).image.show()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
