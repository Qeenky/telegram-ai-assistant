from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime

@dataclass
class MessageDTO:
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[Dict] = None
    timestamp: Optional[str] = None

@dataclass
class DialogueCreateDTO:
    telegram_id: int
    conversation_history: Optional[List[Dict]] = None

@dataclass
class DialogueResponseDTO:
    id: int
    user_id: int
    conversation_history: List[Dict]
    updated_at: datetime
    created_at: datetime

    @classmethod
    def from_orm(cls, dialogue: 'Dialogue') -> 'DialogueResponseDTO':
        return cls(
            id=dialogue.id,
            user_id=dialogue.user_id,
            conversation_history=dialogue.conversation_history or [],
            updated_at=dialogue.updated_at,
            created_at=dialogue.created_at
        )