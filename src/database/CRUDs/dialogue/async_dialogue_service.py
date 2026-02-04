from typing import Optional, List, Dict, Tuple
import logging

from src.database.CRUDs.context_manager import get_db
from src.database.CRUDs.dialogue.dialogue_dto import DialogueResponseDTO
from src.database.CRUDs.dialogue.sqlalchemy_dialogue_repository import SQLAlchemyDialogueRepository
from src.database.CRUDs.dialogue.dialogue_service import DialogueService

logger = logging.getLogger(__name__)


class AsyncDialogueService:

    @classmethod
    async def get_or_create_dialogue(
            cls,
            telegram_id: int,
            initial_history: Optional[List[Dict]] = None
    ) -> Tuple[DialogueResponseDTO, bool]:
        async with get_db() as session:
            repo = SQLAlchemyDialogueRepository(session)
            service = DialogueService(repo)
            return await service.get_or_create_dialogue(telegram_id, initial_history)

    @classmethod
    async def add_message(
            cls,
            telegram_id: int,
            role: str,
            content: str,
            metadata: Optional[Dict] = None
    ) -> DialogueResponseDTO:
        async with get_db() as session:
            repo = SQLAlchemyDialogueRepository(session)
            service = DialogueService(repo)
            return await service.add_message(telegram_id, role, content, metadata)

    @classmethod
    async def get_conversation_history(
            cls,
            telegram_id: int,
            limit: Optional[int] = None
    ) -> List[Dict]:
        async with get_db() as session:
            repo = SQLAlchemyDialogueRepository(session)
            service = DialogueService(repo)
            return await service.get_conversation_history(telegram_id, limit)

    @classmethod
    async def add_user_message(
            cls,
            telegram_id: int,
            content: str,
            metadata: Optional[Dict] = None
    ) -> DialogueResponseDTO:
        return await cls.add_message(
            telegram_id=telegram_id,
            role="user",
            content=content,
            metadata=metadata
        )

    @classmethod
    async def add_assistant_message(
            cls,
            telegram_id: int,
            content: str,
            metadata: Optional[Dict] = None
    ) -> DialogueResponseDTO:
        return await cls.add_message(
            telegram_id=telegram_id,
            role="assistant",
            content=content,
            metadata=metadata
        )

    @classmethod
    async def get_last_messages(
            cls,
            telegram_id: int,
            last_n: int = 10
    ) -> List[Dict]:
        history = await cls.get_conversation_history(telegram_id)
        return history[-last_n:] if history else []

    @classmethod
    async def clear_conversation_history(
            cls,
            telegram_id: int
    ) -> DialogueResponseDTO:
        async with get_db() as session:
            repo = SQLAlchemyDialogueRepository(session)
            dialogue, created = await repo.get_or_create_dialogue(telegram_id)
            dialogue.conversation_history = []
            await session.flush()
            return DialogueResponseDTO.from_orm(dialogue)