from datetime import datetime, timedelta
import asyncio
from sqlalchemy import update
from models import User
from src.database.crud import get_db


async def reset_daily_limits():
    while True:
        now = datetime.utcnow()
        next_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
        sleep_seconds = (next_reset - now).total_seconds()

        await asyncio.sleep(sleep_seconds)

        # Сброс всех пользователей
        async with get_db() as session:
            await session.execute(
                update(User)
                .values(tokens_used_today=0, last_reset_date=datetime.utcnow())
            )
            await session.commit()


async def on_startup(dp):
    asyncio.create_task(reset_daily_limits())
