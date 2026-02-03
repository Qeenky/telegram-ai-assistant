from datetime import datetime, timedelta
import asyncio
from sqlalchemy import update
from src.database.models import User, Subscription
from src.database.crud import get_db


async def reset_daily_limits():
    while True:
        now = datetime.utcnow()
        next_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
        sleep_seconds = (next_reset - now).total_seconds()

        await asyncio.sleep(sleep_seconds)

        async with get_db() as session:
            await session.execute(
                update(User)
                .values(tokens_used_today=0)
            )


async def check_expired_subscriptions():
  while True:
      await asyncio.sleep(3600)
      async with get_db() as session:
          await session.execute(
              update(Subscription)
              .where(Subscription.status == "active")
              .where(Subscription.expires_at <= datetime.utcnow())
              .values(status="expired")
          )