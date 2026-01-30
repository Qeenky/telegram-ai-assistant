from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import logging

from .models import User, Dialogue
from src.config import _Config

DATABASE_URL = _Config.DATABASE_URL
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@contextmanager
def get_db() -> Session:
    """Контекстный менеджер для работы с БД"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise e
    finally:
        db.close()

# TODO: Удалить неиспользуемые функции
def get_or_create_user(session: Session, telegram_id: int, username: Optional[str] = None) -> tuple[User, bool]:
    """
    Получить пользователя или создать нового если не существует.
    Возвращает (user, created), где created = True если пользователь был создан, False если уже существовал
    """
    # Пытаемся найти существующего пользователя
    existing_user = get_user_by_telegram_id(session, telegram_id)

    if existing_user:
        # Обновляем username если он изменился и не пустой
        if username is not None and existing_user.username != username:
            existing_user.username = username

        return existing_user, False
    else:
        # Создаем нового пользователя
        new_user = User(telegram_id=telegram_id, username=username)
        session.add(new_user)
        return new_user, True


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """Получение пользователя по ID"""
    return session.query(User).filter(User.id == user_id).first()


def get_user_by_telegram_id(session: Session, telegram_id: int) -> Optional[User]:
    """Получение пользователя по telegram_id"""
    return session.query(User).filter(User.telegram_id == telegram_id).first()


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    """Получение пользователя по username (частичное совпадение)"""
    return session.query(User).filter(User.username.ilike(f"%{username}%")).first()


def get_all_users(session: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Получение всех пользователей с пагинацией"""
    return session.query(User).offset(skip).limit(limit).all()


def get_users_count(session: Session) -> int:
    """Получение общего количества пользователей"""
    return session.query(User).count()


def get_users_created_after(session: Session, date: datetime) -> List[User]:
    """Получение пользователей, созданных после указанной даты"""
    return session.query(User).filter(User.created_at > date).all()

def search_users(session: Session, telegram_id: Optional[int] = None,
                 username: Optional[str] = None) -> List[User]:
    """Поиск пользователей с фильтрацией"""
    query = session.query(User)

    if telegram_id:
        query = query.filter(User.telegram_id == telegram_id)
    if username:
        query = query.filter(User.username.ilike(f"%{username}%"))

    return query.all()


def update_user(session: Session, user_id: int, **kwargs) -> Optional[User]:
    """
    Обновление пользователя по ID
    kwargs: словарь с полями для обновления
    """
    user = get_user_by_id(session, user_id)
    if not user:
        return None

    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)

    return user


def update_user_by_telegram_id(session: Session, telegram_id: int, **kwargs) -> Optional[User]:
    """Обновление пользователя по telegram_id"""
    user = get_user_by_telegram_id(session, telegram_id)
    if not user:
        return None

    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)

    return user


def update_username(session: Session, user_id: int, username: str) -> Optional[User]:
    """Обновление только username"""
    return update_user(session, user_id, username=username)


def delete_user(session: Session, user_id: int) -> bool:
    """Удаление пользователя по ID"""
    user = get_user_by_id(session, user_id)
    if not user:
        return False

    session.delete(user)
    return True


def delete_user_by_telegram_id(session: Session, telegram_id: int) -> bool:
    """Удаление пользователя по telegram_id"""
    user = get_user_by_telegram_id(session, telegram_id)
    if not user:
        return False

    session.delete(user)
    return True


def delete_all_users(session: Session) -> int:
    """Удаление всех пользователей"""
    count = get_users_count(session)
    session.query(User).delete()
    return count


def delete_users_by_ids(session: Session, user_ids: List[int]) -> int:
    """Удаление нескольких пользователей по IDs"""
    deleted_count = session.query(User).filter(User.id.in_(user_ids)).delete()
    return deleted_count


# TODO: Удалить неиспользуемые методы
class DialogueCRUD:
    @staticmethod
    def get_or_create_dialogue(
            session: Session,
            telegram_id: int,
            initial_history: Optional[List[Dict]] = None
    ) -> Tuple[Dialogue, bool]:
        """
        Получить диалог или создать новый если не существует.

        Args:
            session: SQLAlchemy сессия
            telegram_id: ID пользователя в Telegram
            initial_history: Начальная история диалога (если создается новый)

        Returns:
            tuple: (dialogue, created), где created = True если диалог был создан, False если уже существовал

        Raises:
            ValueError: Если пользователь с таким telegram_id не найден
        """

        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            raise ValueError(
                f"Пользователь с telegram_id={telegram_id} не найден. Сначала зарегистрируйтесь через /start")

        existing_dialogue = session.query(Dialogue).filter(Dialogue.user_id == user.id).first()

        if existing_dialogue:
            return existing_dialogue, False
        else:
            new_dialogue = Dialogue(
                user_id=user.id,
                conversation_history=initial_history or []
            )
            session.add(new_dialogue)
            session.flush()
            return new_dialogue, True

    @staticmethod
    def get_dialogue_by_user_id(session: Session, user_id: int) -> Optional[Dialogue]:
        """Получить диалог по ID пользователя"""
        return session.query(Dialogue).filter_by(user_id=user_id).first()

    @staticmethod
    def get_dialogue_by_telegram_id(session: Session, telegram_id: int) -> Optional[Dialogue]:
        """Получить диалог по telegram_id через связь с User"""
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            return session.query(Dialogue).filter_by(user_id=user.id).first()
        return None

    @staticmethod
    def add_message(
            session: Session,
            telegram_id: int,
            role: str,  # 'user', 'assistant', 'system'
            content: str,
            metadata: Optional[Dict] = None
    ) -> Dialogue:
        """
        Добавить сообщение в историю диалога
        """

        dialogue_result = DialogueCRUD.get_or_create_dialogue(session, telegram_id)

        if isinstance(dialogue_result, tuple):
            dialogue, created = dialogue_result
        else:
            dialogue = dialogue_result

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

        session.add(dialogue)
        session.flush()

        session.refresh(dialogue)

        return dialogue

    @staticmethod
    def get_conversation_history(
            session: Session,
            telegram_id: int,
            limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Получить историю диалога
        """
        result = DialogueCRUD.get_or_create_dialogue(session, telegram_id)

        if isinstance(result, tuple):
            dialogue, created = result
        else:
            dialogue = result

        if limit and len(dialogue.conversation_history) > limit:
            return dialogue.conversation_history[-limit:]

        return dialogue.conversation_history

    @staticmethod
    def clear_conversation_history(session: Session, telegram_id: int) -> Dialogue:
        """Очистить историю диалога"""
        result = DialogueCRUD.get_or_create_dialogue(session, telegram_id)

        if isinstance(result, tuple):
            dialogue, created = result
        else:
            dialogue = result

        dialogue.conversation_history = []
        dialogue.updated_at = datetime.utcnow()

        session.add(dialogue)
        session.flush()

        session.refresh(dialogue)

        return dialogue

    @staticmethod
    def update_conversation_history(
            session: Session,
            telegram_id: int,
            new_history: List[Dict]
    ) -> Dialogue:
        """Полностью обновить историю диалога"""
        result = DialogueCRUD.get_or_create_dialogue(session, telegram_id)

        if isinstance(result, tuple):
            dialogue, created = result
        else:
            dialogue = result

        dialogue.conversation_history = new_history
        dialogue.updated_at = datetime.utcnow()

        session.add(dialogue)
        session.flush()

        session.refresh(dialogue)

        return dialogue

    @staticmethod
    def delete_dialogue(session: Session, user_id: int) -> bool:
        """Удалить диалог пользователя"""
        dialogue = session.query(Dialogue).filter_by(user_id=user_id).first()
        if dialogue:
            session.delete(dialogue)
            session.flush()
            return True
        return False

    @staticmethod
    def get_dialogues_older_than(
            session: Session,
            days: int = 30
    ) -> List[Dialogue]:
        """Получить диалоги, не обновлявшиеся более N дней"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        return session.query(Dialogue).filter(Dialogue.updated_at < cutoff_date).all()

    @staticmethod
    def get_last_user_message(
            session: Session,
            telegram_id: int
    ) -> Optional[Dict]:
        """Получить последнее сообщение пользователя"""
        result = DialogueCRUD.get_or_create_dialogue(session, telegram_id)

        if isinstance(result, tuple):
            dialogue, created = result
        else:
            dialogue = result

        for message in reversed(dialogue.conversation_history):
            if message.get("role") == "user":
                return message

        return None

    @staticmethod
    def get_conversation_summary(
            session: Session,
            telegram_id: int
    ) -> Dict[str, Any]:
        """Получить статистику по диалогу"""
        result = DialogueCRUD.get_or_create_dialogue(session, telegram_id)

        if isinstance(result, tuple):
            dialogue, created = result
        else:
            dialogue = result

        user_messages = [
            m for m in dialogue.conversation_history
            if m.get("role") == "user"
        ]
        assistant_messages = [
            m for m in dialogue.conversation_history
            if m.get("role") == "assistant"
        ]

        return {
            "dialogue_id": dialogue.id,
            "user_id": dialogue.user_id,
            "total_messages": len(dialogue.conversation_history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "last_updated": dialogue.updated_at,
            "created_at": dialogue.created_at,
        }

    @staticmethod
    def refresh(session: Session, dialogue: Dialogue) -> Dialogue:
        """Обновить объект диалога из базы данных"""
        session.refresh(dialogue)
        return dialogue