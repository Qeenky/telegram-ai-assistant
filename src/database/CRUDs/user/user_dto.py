from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class UserCreateDTO:
    telegram_id: int
    username: Optional[str] = None
    daily_token_limit: int = 10000


@dataclass
class UserUpdateDTO:
    username: Optional[str] = None
    daily_token_limit: Optional[int] = None


@dataclass
class UserTokenUsageDTO:
    telegram_id: int
    tokens_used: int


@dataclass
class UserResponseDTO:
    id: int
    telegram_id: int
    username: Optional[str]
    daily_token_limit: int
    tokens_used_today: int
    created_at: datetime

    @classmethod
    def from_orm(cls, user: 'User') -> 'UserResponseDTO':
        """Конвертация из ORM модели в DTO"""
        return cls(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            daily_token_limit=user.daily_token_limit,
            tokens_used_today=user.tokens_used_today,
            created_at=user.created_at
        )