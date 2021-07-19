import asyncio

SPACING = 12

FONT_BLACK = 'fonts/Roboto-Black.ttf'
FONT_BOLD = 'fonts/Roboto-Bold.ttf'
FONT_REGULAR = 'fonts/Roboto-Regular.ttf'
FONT_LIGHT = 'fonts/Roboto-Light.ttf'


async def main():
    from bot.card.PlayerCard import RankCard
    (await RankCard(username='threeleaves').render()).image.show()

if __name__ == '__main__':
    asyncio.run(main())
