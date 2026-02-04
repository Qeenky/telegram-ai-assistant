from typing import Optional
from datetime import datetime
import logging

from src.database.CRUDs.subscription.subscription_dto import (
    SubscriptionCreateDTO,
    SubscriptionResponseDTO,
    SubscriptionType
)
from src.database.CRUDs.subscription.subscription_repository_interface import ISubscriptionRepository

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, subscription_repository: ISubscriptionRepository):
        self._subscription_repo = subscription_repository

    async def get_active_subscription(self, telegram_id: int) -> Optional[SubscriptionResponseDTO]:
        subscription = await self._subscription_repo.get_active_subscription(telegram_id)
        if subscription:
            return SubscriptionResponseDTO.from_orm(subscription)
        return None

    async def create_or_extend_subscription(
            self,
            telegram_id: int,
            subscription_type: SubscriptionType,
            days: int
    ) -> Optional[SubscriptionResponseDTO]:
        subscription_data = SubscriptionCreateDTO(
            telegram_id=telegram_id,
            subscription_type=subscription_type,
            days=days
        )

        subscription = await self._subscription_repo.create_subscription(subscription_data)
        if subscription:
            return SubscriptionResponseDTO.from_orm(subscription)
        return None

    async def has_active_premium(self, telegram_id: int) -> bool:
        subscription = await self.get_active_subscription(telegram_id)
        if subscription and subscription.type == SubscriptionType.PREMIUM:
            return True
        return False

    async def get_subscription_info(self, telegram_id: int) -> str:
        subscription = await self.get_active_subscription(telegram_id)

        if not subscription:
            return "У вас нет активной подписки"

        days_left = (subscription.expires_at - datetime.utcnow()).days
        status_text = {
            SubscriptionType.BASIC: "Базовая",
            SubscriptionType.PREMIUM: "Премиум",
            SubscriptionType.TRIAL: "Пробная"
        }.get(subscription.type, subscription.type)

        return (
            f"📋 Подписка: {status_text}\n"
            f"📅 Статус: {subscription.status}\n"
            f"⏳ Истекает: {subscription.expires_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📆 Осталось дней: {days_left}"
        )

    async def expire_old_subscriptions(self) -> int:
        return await self._subscription_repo.expire_old_subscriptions()