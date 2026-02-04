from typing import Optional, List, Dict, Tuple
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, Dialogue
from src.database.CRUDs.dialogue.dialogue_repository_interface import IDialogueRepository


class SQLAlchemyDialogueRepository(IDialogueRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_or_create_dialogue(
            self,
            telegram_id: int,
            initial_history: Optional[List[Dict]] = None
    ) -> Tuple[Dialogue, bool]:
        user = await self._session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user:
            raise ValueError(
                f"Пользователь с telegram_id={telegram_id} не найден. "
                "Сначала зарегистрируйтесь через /start"
            )

        existing_dialogue = await self._session.scalar(
            select(Dialogue).where(Dialogue.user_id == user.id)
        )

        if existing_dialogue:
            return existing_dialogue, False
        else:
            new_dialogue = Dialogue(
                user_id=user.id,
                conversation_history=initial_history or []
            )
            self._session.add(new_dialogue)
            await self._session.flush()
            return new_dialogue, True

    async def add_message(
            self,
            telegram_id: int,
            role: str,
            content: str,
            metadata: Optional[Dict] = None
    ) -> Dialogue:
        dialogue, created = await self.get_or_create_dialogue(telegram_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }

        if metadata:
            message["metadata"] = metadata

        current_history = dialogue.conversation_history.copy() if dialogue.conversation_history else []
        current_history.append(message)
        dialogue.conversation_history = current_history
        dialogue.updated_at = datetime.utcnow()
        await self._session.flush()

        return dialogue

    async def get_conversation_history(
            self,
            telegram_id: int,
            limit: Optional[int] = None
    ) -> List[Dict]:
        dialogue, created = await self.get_or_create_dialogue(telegram_id)

        if limit and len(dialogue.conversation_history) > limit:
            return dialogue.conversation_history[-limit:]

        return dialogue.conversation_history or []

    async def refresh_dialogue(self, dialogue: Dialogue) -> Dialogue:
        await self._session.refresh(dialogue)
        return dialogue