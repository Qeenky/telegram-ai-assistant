import logging
from datetime import datetime, timedelta
import asyncio
from sqlalchemy import update, select
from src.database.models import User, Subscription
from src.database.CRUDs.context_manager import get_db


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
        await asyncio.sleep(60)
        current_time = datetime.utcnow()
        async with get_db() as session:
            try:
                stmt = select(Subscription.user_id).where(
                    Subscription.status == "active",
                    Subscription.expires_at <= current_time
                ).distinct()

                result = await session.execute(stmt)
                expired_user_ids = [row[0] for row in result]

                if expired_user_ids:
                    await session.execute(
                        update(Subscription)
                        .where(Subscription.status == "active")
                        .where(Subscription.expires_at <= current_time)
                        .values(status="expired")
                    )
                    await session.execute(
                        update(User)
                        .where(User.id.in_(expired_user_ids))
                        .values(daily_token_limit=10000)
                    )
                    await session.commit()
                    logging.info(f"Updated {len(expired_user_ids)} expired subscriptions")

            except Exception as e:
                await session.rollback()
                logging.error(f"Error: {e}")