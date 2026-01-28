from aiogram import Bot, Dispatcher
from config import _Config
from bot.handlers import main_router
import asyncio, logging


bot = Bot(token=_Config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

dp.include_router(main_router)

async def start_bot():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"File main.py, Error: {e}")


async def main():
    await start_bot()

if __name__ == '__main__':
    asyncio.run(main())