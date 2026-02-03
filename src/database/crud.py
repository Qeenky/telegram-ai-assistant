from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

import logging

from .models import User, Dialogue, Subscription
from src.config import _Config

DATABASE_URL = _Config.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from contextlib import asynccontextmanager



@asynccontextmanager
async def get_db() -> AsyncSession:
    """Контекстный менеджер для работы с БД"""
    session = SessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        await session.close()


async def get_or_create_user(
        session: AsyncSession,
        telegram_id: int,
        daily_token_limit: int,
        username: Optional[str] = None
) -> tuple[User, bool]:
    """
    Получить пользователя или создать нового если не существует.
    Возвращает (user, created), где created = True если пользователь был создан
    """
    try:
        existing_user = await get_user_by_telegram_id(session, telegram_id)

        if existing_user:
            if username is not None and existing_user.username != username:
                existing_user.username = username
            return existing_user, False
        else:
            new_user = User(
                telegram_id=telegram_id,
                username=username,
                daily_token_limit=daily_token_limit
            )
            session.add(new_user)
            await session.flush()
            return new_user, True

    except Exception as e:
        logger.error(f"Ошибка в get_or_create_user для telegram_id={telegram_id}: {e}")
        raise


async def add_tokens_used(session: AsyncSession, telegram_id: int, tokens_used: int) -> bool:
    """Добавление использованных токенов пользователю"""
    try:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"Пользователь {telegram_id} не найден")
            return False

        user.tokens_used_today += tokens_used
        return True

    except Exception as e:
        logger.error(f"Ошибка при добавлении токенов: {e}")
        return False

async def check_tokens_used(session: AsyncSession, telegram_id: int) -> bool:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"Пользователь {telegram_id} не найден")
        return False

    if user.tokens_used_today < user.daily_token_limit:
        return True
    else:
        return False


async def check_limit_tokens(session: AsyncSession, telegram_id: int) -> str:
    """Проверка лимита токенов пользователя"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"Пользователь {telegram_id} не найден")
        return "Зарегистрируйтесь с помощью команды /start, или напишите в поддержку"

    return f"{user.tokens_used_today} / {user.daily_token_limit} tokens."


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Получение пользователя по ID"""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Получение пользователя по telegram_id"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()



class DialogueCRUD:
    @staticmethod
    async def get_or_create_dialogue(
            session: AsyncSession,
            telegram_id: int,
            initial_history: Optional[List[Dict]] = None
    ) -> Tuple[Dialogue, bool]:
        """
        Получить диалог или создать новый если не существует.
        """
        user = await session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user:
            raise ValueError(
                f"Пользователь с telegram_id={telegram_id} не найден. "
                "Сначала зарегистрируйтесь через /start"
            )

        existing_dialogue = await session.scalar(
            select(Dialogue).where(Dialogue.user_id == user.id)
        )

        if existing_dialogue:
            return existing_dialogue, False
        else:
            new_dialogue = Dialogue(
                user_id=user.id,
                conversation_history=initial_history or []
            )
            session.add(new_dialogue)
            await session.flush()
            return new_dialogue, True

    @staticmethod
    async def add_message(
            session: AsyncSession,
            telegram_id: int,
            role: str,  # 'user', 'assistant', 'system'
            content: str,
            metadata: Optional[Dict] = None
    ) -> Dialogue:
        """
        Добавить сообщение в историю диалога
        """
        dialogue, created = await DialogueCRUD.get_or_create_dialogue(session, telegram_id)

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
        await session.flush()

        return dialogue

    @staticmethod
    async def get_conversation_history(
            session: AsyncSession,
            telegram_id: int,
            limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Получить историю диалога
        """
        result = await DialogueCRUD.get_or_create_dialogue(session, telegram_id)

        if isinstance(result, tuple):
            dialogue, created = result
        else:
            dialogue = result

        if limit and len(dialogue.conversation_history) > limit:
            return dialogue.conversation_history[-limit:]

        return dialogue.conversation_history


    @staticmethod
    async def refresh(session: AsyncSession, dialogue: Dialogue) -> Dialogue:
        """Обновить объект диалога из базы данных"""
        await session.refresh(dialogue)
        return dialogue


class SubscriptionsCRUD:
    @staticmethod
    async def create_subscription(telegram_id: int, subscription_type: str, days: int):
        from sqlalchemy import select
        from datetime import datetime, timedelta

        async with get_db() as session:
            user_stmt = select(User).where(User.telegram_id == telegram_id)
            user = await session.scalar(user_stmt)

            if not user:
                return None

            subscription = Subscription(
                user_id=user.id,
                type=subscription_type,
                status="active",
                starts_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=days)
            )

            session.add(subscription)
            await session.commit()
            await session.refresh(subscription)

            return subscription

    @staticmethod
    async def get_active_subscription(telegram_id: int):
        async with get_db() as session:
            stmt = (
                select(Subscription)
                .join(User, Subscription.user_id == User.id)
                .where(
                    User.telegram_id == telegram_id,
                    Subscription.status == "active"
                )
                .order_by(Subscription.expires_at.desc())
            )
            result = await session.scalar(stmt)

            return result