from aiogram import Bot, Dispatcher
from config import _Config
from bot.handlers import main_router
from src.database.tasks import reset_daily_limits
import asyncio, logging


bot = Bot(token=_Config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

dp.include_router(main_router)


async def main():
    reset_task = asyncio.create_task(reset_daily_limits())

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Bot stopped with error: {e}")
    finally:
        reset_task.cancel()
        try:
            await reset_task
        except asyncio.CancelledError:
            pass
        logging.info("Background tasks stopped")

if __name__ == '__main__':
    asyncio.run(main())