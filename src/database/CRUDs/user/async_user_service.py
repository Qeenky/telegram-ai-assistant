from typing import Optional
import logging

from src.database.CRUDs.context_manager import get_db
from src.database.CRUDs.user.user_dto import UserResponseDTO
from src.database.CRUDs.user.sqlalchemy_user_repository import SQLAlchemyUserRepository
from src.database.CRUDs.user.user_service import UserService

logger = logging.getLogger(__name__)


class AsyncUserService:
    """
    Главный сервис для работы с пользователями.
    """

    @classmethod
    async def get_user_by_telegram_id(cls, telegram_id: int) -> Optional[UserResponseDTO]:
        async with get_db() as session:
            repo = SQLAlchemyUserRepository(session)
            service = UserService(repo)
            return await service.get_user_by_telegram_id(telegram_id)

    @classmethod
    async def get_or_create_user(
            cls,
            telegram_id: int,
            username: Optional[str] = None,
            daily_token_limit: int = 10000
    ) -> tuple[Optional[UserResponseDTO], bool]:
        async with get_db() as session:
            repo = SQLAlchemyUserRepository(session)
            user, created = await repo.get_or_create(
                telegram_id=telegram_id,
                username=username,
                daily_token_limit=daily_token_limit
            )
            if user:
                return UserResponseDTO.from_orm(user), created
            return None, False

    @classmethod
    async def add_tokens_used(cls, telegram_id: int, tokens_used: int) -> bool:
        async with get_db() as session:
            repo = SQLAlchemyUserRepository(session)
            return await repo.add_tokens_used(telegram_id, tokens_used)


    @classmethod
    async def check_limit_tokens(cls, telegram_id: int) -> tuple[bool, str]:
        async with get_db() as session:
            repo = SQLAlchemyUserRepository(session)
            has_tokens, status = await repo.check_token_limit(telegram_id)
            if has_tokens is False and "не найден" in status:
                return "Зарегистрируйтесь с помощью команды /start, или напишите в поддержку"
            return (has_tokens, status)