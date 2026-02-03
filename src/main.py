from aiogram import Bot, Dispatcher
from config import _Config
from bot.handlers import main_router
from src.database.tasks import reset_daily_limits, check_expired_subscriptions
import asyncio, logging


bot = Bot(token=_Config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

dp.include_router(main_router)


async def main():
    reset_task = asyncio.create_task(reset_daily_limits())
    check_sub_task = asyncio.create_task(check_expired_subscriptions())
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Bot stopped with error: {e}")
    finally:
        reset_task.cancel()
        check_sub_task.cancel()
        try:
            await asyncio.gather(
                reset_task,
                check_sub_task,
                return_exceptions=True
            )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"Error while stopping tasks: {e}")
        logging.info("Background tasks stopped")

if __name__ == '__main__':
    asyncio.run(main())