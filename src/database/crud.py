from datetime import datetime, timedelta

from sqlalchemy import select

import logging

from .models import User, Subscription
from .CRUDs.context_manager import get_db



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SubscriptionsCRUD:
    @staticmethod
    async def create_subscription(telegram_id: int, subscription_type: str, days: int):
        """Создать или продлить подписку пользователю"""
        async with get_db() as session:
            try:
                user = await session.scalar(
                    select(User).where(User.telegram_id == telegram_id)
                )
                if not user:
                    return None

                current_time = datetime.utcnow()
                existing_sub = await session.scalar(
                    select(Subscription)
                    .where(
                        Subscription.user_id == user.id,
                        Subscription.status == "active"
                    )
                    .order_by(Subscription.expires_at.desc())
                )

                if existing_sub and existing_sub.expires_at > current_time:
                    new_expires_at = existing_sub.expires_at + timedelta(days=days)

                    if subscription_type != existing_sub.type:
                        existing_sub.type = subscription_type

                    existing_sub.expires_at = new_expires_at
                    result_sub = existing_sub
                    action = "extended"

                    if subscription_type == "premium":
                        user.daily_token_limit = 49999

                else:
                    new_expires_at = current_time + timedelta(days=days)
                    if existing_sub:
                        existing_sub.expires_at = new_expires_at
                        existing_sub.status = "active"
                        existing_sub.type = subscription_type
                        existing_sub.starts_at = current_time
                        result_sub = existing_sub
                        action = "renewed"
                    else:
                        new_sub = Subscription(
                            user_id=user.id,
                            type=subscription_type,
                            status="active",
                            starts_at=current_time,
                            expires_at=new_expires_at
                        )
                        session.add(new_sub)
                        result_sub = new_sub
                        action = "created"

                    if subscription_type == "premium":
                        user.daily_token_limit = 49999

                logging.info(f"Subscription {action} for user {telegram_id}, expires at {result_sub.expires_at}")
                return result_sub
            except Exception as e:
                logging.error(f"Error creating/extending subscription: {e}")
                return None


    @staticmethod
    async def get_active_subscription(telegram_id: int):
        async with get_db() as session:
            stmt = (
                select(Subscription)
                .join(User, Subscription.user_id == User.id)
                .where(
                    User.telegram_id == telegram_id,
                    Subscription.status == "active"
                )
                .order_by(Subscription.expires_at.desc())
            )
            result = await session.scalar(stmt)

            return result