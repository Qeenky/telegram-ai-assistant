from abc import ABC, abstractmethod
from typing import Optional

from src.database.models import Subscription
from src.database.CRUDs.subscription.subscription_dto import (
    SubscriptionCreateDTO
)


class ISubscriptionRepository(ABC):
    @abstractmethod
    async def get_active_subscription(self, telegram_id: int) -> Optional[Subscription]:
        pass

    @abstractmethod
    async def create_subscription(self, subscription_data: SubscriptionCreateDTO) -> Optional[Subscription]:
        pass

    @abstractmethod
    async def expire_old_subscriptions(self) -> int:
        pass