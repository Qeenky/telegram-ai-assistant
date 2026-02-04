from typing import Optional
import logging

from src.database.CRUDs.context_manager import get_db
from src.database.CRUDs.subscription.subscription_dto import (
    SubscriptionResponseDTO,
    SubscriptionType
)
from src.database.CRUDs.subscription.sqlalchemy_subscription_repository import SQLAlchemySubscriptionRepository
from src.database.CRUDs.subscription.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class AsyncSubscriptionService:
    @classmethod
    async def create_subscription(
            cls,
            telegram_id: int,
            subscription_type: str,
            days: int
    ) -> Optional[SubscriptionResponseDTO]:
        try:
            sub_type = SubscriptionType(subscription_type.lower()) # Конвертируем строку в enum
        except ValueError:
            logger.error(f"Invalid subscription type: {subscription_type}")
            return None

        async with get_db() as session:
            repo = SQLAlchemySubscriptionRepository(session)
            service = SubscriptionService(repo)
            return await service.create_or_extend_subscription(
                telegram_id=telegram_id,
                subscription_type=sub_type,
                days=days
            )

    @classmethod
    async def get_active_subscription(cls, telegram_id: int) -> Optional[SubscriptionResponseDTO]:
        async with get_db() as session:
            repo = SQLAlchemySubscriptionRepository(session)
            service = SubscriptionService(repo)
            return await service.get_active_subscription(telegram_id)

    @classmethod
    async def has_active_premium(cls, telegram_id: int) -> bool:
        subscription = await cls.get_active_subscription(telegram_id)
        if subscription and subscription.type == SubscriptionType.PREMIUM:
            return True
        return False

    @classmethod
    async def get_subscription_info(cls, telegram_id: int) -> str:
        async with get_db() as session:
            repo = SQLAlchemySubscriptionRepository(session)
            service = SubscriptionService(repo)
            return await service.get_subscription_info(telegram_id)

    @classmethod
    async def expire_old_subscriptions(cls) -> int:
        async with get_db() as session:
            repo = SQLAlchemySubscriptionRepository(session)
            service = SubscriptionService(repo)
            return await service.expire_old_subscriptions()

    @classmethod
    async def create_premium_subscription(cls, telegram_id: int, days: int = 30) -> Optional[SubscriptionResponseDTO]:
        return await cls.create_subscription(
            telegram_id=telegram_id,
            subscription_type=SubscriptionType.PREMIUM,
            days=days
        )

    @classmethod
    async def create_basic_subscription(cls, telegram_id: int, days: int = 30) -> Optional[SubscriptionResponseDTO]:
        return await cls.create_subscription(
            telegram_id=telegram_id,
            subscription_type=SubscriptionType.BASIC,
            days=days
        )

    @classmethod
    async def get_user_token_limit(cls, telegram_id: int) -> int:
        from src.database.CRUDs.user import AsyncUserService

        user = await AsyncUserService.get_user_by_telegram_id(telegram_id)
        if not user:
            return 10000

        has_premium = await cls.has_active_premium(telegram_id)
        if has_premium:
            return 49999
        return user.daily_token_limit