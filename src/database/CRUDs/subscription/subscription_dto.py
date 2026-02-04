from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class SubscriptionType(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    TRIAL = "trial"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELED = "canceled"

@dataclass
class SubscriptionCreateDTO:
    telegram_id: int
    subscription_type: SubscriptionType
    days: int
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

@dataclass
class SubscriptionResponseDTO:
    id: int
    user_id: int
    type: str
    status: str
    starts_at: datetime
    expires_at: datetime
    created_at: datetime

    @classmethod
    def from_orm(cls, subscription: 'Subscription') -> 'SubscriptionResponseDTO':
        return cls(
            id=subscription.id,
            user_id=subscription.user_id,
            type=subscription.type,
            status=subscription.status,
            starts_at=subscription.starts_at,
            expires_at=subscription.expires_at,
            created_at=subscription.created_at
        )