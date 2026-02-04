from abc import ABC, abstractmethod
from typing import Optional
from src.database.models import User
from src.database.CRUDs.user.user_dto import UserCreateDTO, UserUpdateDTO


class IUserRepository(ABC):

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def create(self, user_data: UserCreateDTO) -> User:
        pass

    @abstractmethod
    async def update(self, user_id: int, user_data: UserUpdateDTO) -> Optional[User]:
        pass

    @abstractmethod
    async def update_username(self, telegram_id: int, username: str) -> bool:
        pass

    @abstractmethod
    async def add_tokens_used(self, telegram_id: int, tokens: int) -> bool:
        pass

    @abstractmethod
    async def reset_daily_tokens(self) -> int:
        pass

    @abstractmethod
    async def get_or_create(
            self,
            telegram_id: int,
            username: Optional[str] = None,
            daily_token_limit: int = 10000
    ) -> tuple[User, bool]:
        pass

    @abstractmethod
    async def check_token_limit(self, telegram_id: int) -> tuple[bool, str]:
        pass