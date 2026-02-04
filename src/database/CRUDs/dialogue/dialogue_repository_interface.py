from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Tuple
from src.database.models import Dialogue


class IDialogueRepository(ABC):

    @abstractmethod
    async def get_or_create_dialogue(
            self,
            telegram_id: int,
            initial_history: Optional[List[Dict]] = None
    ) -> Tuple[Dialogue, bool]:
        pass

    @abstractmethod
    async def add_message(
            self,
            telegram_id: int,
            role: str,
            content: str,
            metadata: Optional[Dict] = None
    ) -> Dialogue:
        pass

    @abstractmethod
    async def get_conversation_history(
            self,
            telegram_id: int,
            limit: Optional[int] = None
    ) -> List[Dict]:
        pass

    @abstractmethod
    async def refresh_dialogue(self, dialogue: Dialogue) -> Dialogue:
        pass