from datetime import datetime
from typing import Optional, List

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import logging

from .models import User
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