from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database.models import User, Subscription
from src.database.CRUDs.subscription.subscription_dto import (
    SubscriptionCreateDTO,
    SubscriptionType,
    SubscriptionStatus
)
from src.database.CRUDs.subscription.subscription_repository_interface import ISubscriptionRepository

logger = logging.getLogger(__name__)


class SQLAlchemySubscriptionRepository(ISubscriptionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_active_subscription(self, telegram_id: int) -> Optional[Subscription]:
        stmt = (
            select(Subscription)
            .join(User, Subscription.user_id == User.id)
            .where(
                User.telegram_id == telegram_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
            .order_by(Subscription.expires_at.desc())
        )
        result = await self._session.scalar(stmt)
        return result

    async def create_subscription(self, subscription_data: SubscriptionCreateDTO) -> Optional[Subscription]:
        try:
            user = await self._session.scalar(
                select(User).where(User.telegram_id == subscription_data.telegram_id)
            )
            if not user:
                logger.error(f"User {subscription_data.telegram_id} not found")
                return None

            current_time = datetime.utcnow()
            existing_sub = await self.get_active_subscription(subscription_data.telegram_id)

            if existing_sub and existing_sub.expires_at > current_time:
                new_expires_at = existing_sub.expires_at + timedelta(days=subscription_data.days)

                if subscription_data.subscription_type != existing_sub.type:
                    existing_sub.type = subscription_data.subscription_type

                existing_sub.expires_at = new_expires_at
                result_sub = existing_sub
                action = "extended"

                if subscription_data.subscription_type == SubscriptionType.PREMIUM:
                    user.daily_token_limit = 49999

            else:
                new_expires_at = current_time + timedelta(days=subscription_data.days)

                if existing_sub:
                    existing_sub.expires_at = new_expires_at
                    existing_sub.status = SubscriptionStatus.ACTIVE
                    existing_sub.type = subscription_data.subscription_type
                    existing_sub.starts_at = current_time
                    result_sub = existing_sub
                    action = "renewed"
                else:
                    new_sub = Subscription(
                        user_id=user.id,
                        type=subscription_data.subscription_type,
                        status=SubscriptionStatus.ACTIVE,
                        starts_at=current_time,
                        expires_at=new_expires_at
                    )
                    self._session.add(new_sub)
                    result_sub = new_sub
                    action = "created"

                if subscription_data.subscription_type == SubscriptionType.PREMIUM:
                    user.daily_token_limit = 49999

            logger.info(f"Subscription {action} for user {subscription_data.telegram_id}, "
                        f"expires at {result_sub.expires_at}")
            return result_sub

        except Exception as e:
            logger.error(f"Error creating/extending subscription: {e}")
            return None

    async def expire_old_subscriptions(self) -> int:
        current_time = datetime.utcnow()
        result = await self._session.execute(
            update(Subscription)
            .where(
                and_(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.expires_at < current_time
                )
            )
            .values(status=SubscriptionStatus.EXPIRED)
            .returning(Subscription.id)
        )
        expired_count = len(result.all())
        if expired_count > 0:
            logger.info(f"Expired {expired_count} subscriptions")
        return expired_count