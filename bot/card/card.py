import asyncio

SPACING = 12

FONT_BLACK = 'fonts/Roboto-Black.ttf'
FONT_BOLD = 'fonts/Roboto-Bold.ttf'
FONT_REGULAR = 'fonts/Roboto-Regular.ttf'
FONT_LIGHT = 'fonts/Roboto-Light.ttf'

FONT_MC_BOLD = 'fonts/Minecraft-Bold.otf'
FONT_MC_REGULAR = 'fonts/Minecraft-Regular.otf'


async def main():
    from bot.card.BalanceCard import BalanceCard
    (await BalanceCard(username='keyutedev').render()).image.show()

if __name__ == '__main__':
    asyncio.run(main())
