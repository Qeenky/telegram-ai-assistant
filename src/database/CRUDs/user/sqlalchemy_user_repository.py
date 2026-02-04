from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.database.CRUDs.user.user_dto import UserCreateDTO, UserUpdateDTO
from src.database.CRUDs.user.user_repository_interface import IUserRepository


class SQLAlchemyUserRepository(IUserRepository):
    """Реализация репозитория пользователей на SQLAlchemy"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreateDTO) -> User:
        user = User(
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            daily_token_limit=user_data.daily_token_limit
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def update(self, user_id: int, user_data: UserUpdateDTO) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = {}
        if user_data.username is not None:
            update_data['username'] = user_data.username
        if user_data.daily_token_limit is not None:
            update_data['daily_token_limit'] = user_data.daily_token_limit

        if update_data:
            await self._session.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
            )
            await self._session.flush()
            await self._session.refresh(user)

        return user

    async def update_username(self, telegram_id: int, username: str) -> bool:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return False

        user.username = username
        return True

    async def add_tokens_used(self, telegram_id: int, tokens: int) -> bool:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return False

        user.tokens_used_today += tokens
        return True

    async def reset_daily_tokens(self) -> int:
        result = await self._session.execute(
            update(User)
            .values(tokens_used_today=0)
            .returning(User.id)
        )
        return len(result.all())

    async def get_or_create(
            self,
            telegram_id: int,
            username: Optional[str] = None,
            daily_token_limit: int = 10000
    ) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)

        if user:
            if username is not None and user.username != username:
                user.username = username
            return user, False
        else:
            user_data = UserCreateDTO(
                telegram_id=telegram_id,
                username=username,
                daily_token_limit=daily_token_limit
            )
            new_user = await self.create(user_data)
            return new_user, True

    async def check_token_limit(self, telegram_id: int) -> tuple[bool, str]:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return False, "Пользователь не найден"

        has_tokens = user.tokens_used_today < user.daily_token_limit
        status = f"{user.tokens_used_today}/{user.daily_token_limit} токенов"
        return has_tokens, status