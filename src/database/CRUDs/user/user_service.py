from typing import Optional
import logging

from src.database.CRUDs.user.user_dto import UserResponseDTO
from src.database.CRUDs.user.user_repository_interface import IUserRepository

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_repository: IUserRepository):
        self._user_repo = user_repository

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[UserResponseDTO]:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user:
            return UserResponseDTO.from_orm(user)
        return None

