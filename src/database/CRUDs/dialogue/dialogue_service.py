from typing import Optional, List, Dict, Tuple
import logging

from src.database.CRUDs.dialogue.dialogue_dto import DialogueResponseDTO
from src.database.CRUDs.dialogue.dialogue_repository_interface import IDialogueRepository

logger = logging.getLogger(__name__)


class DialogueService:
    def __init__(self, dialogue_repository: IDialogueRepository):
        self._dialogue_repo = dialogue_repository

    async def get_or_create_dialogue(
            self,
            telegram_id: int,
            initial_history: Optional[List[Dict]] = None
    ) -> Tuple[DialogueResponseDTO, bool]:
        dialogue, created = await self._dialogue_repo.get_or_create_dialogue(
            telegram_id=telegram_id,
            initial_history=initial_history
        )
        return DialogueResponseDTO.from_orm(dialogue), created

    async def add_message(
            self,
            telegram_id: int,
            role: str,
            content: str,
            metadata: Optional[Dict] = None
    ) -> DialogueResponseDTO:
        dialogue = await self._dialogue_repo.add_message(
            telegram_id=telegram_id,
            role=role,
            content=content,
            metadata=metadata
        )
        return DialogueResponseDTO.from_orm(dialogue)

    async def get_conversation_history(
            self,
            telegram_id: int,
            limit: Optional[int] = None
    ) -> List[Dict]:
        return await self._dialogue_repo.get_conversation_history(
            telegram_id=telegram_id,
            limit=limit
        )