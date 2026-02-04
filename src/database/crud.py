from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from .models import User, Dialogue, Subscription
from .CRUDs.context_manager import get_db



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        """Создать или продлить подписку пользователю"""
        async with get_db() as session:
            try:
                user = await session.scalar(
                    select(User).where(User.telegram_id == telegram_id)
                )
                if not user:
                    return None

                current_time = datetime.utcnow()
                existing_sub = await session.scalar(
                    select(Subscription)
                    .where(
                        Subscription.user_id == user.id,
                        Subscription.status == "active"
                    )
                    .order_by(Subscription.expires_at.desc())
                )

                if existing_sub and existing_sub.expires_at > current_time:
                    new_expires_at = existing_sub.expires_at + timedelta(days=days)

                    if subscription_type != existing_sub.type:
                        existing_sub.type = subscription_type

                    existing_sub.expires_at = new_expires_at
                    result_sub = existing_sub
                    action = "extended"

                    if subscription_type == "premium":
                        user.daily_token_limit = 49999

                else:
                    new_expires_at = current_time + timedelta(days=days)
                    if existing_sub:
                        existing_sub.expires_at = new_expires_at
                        existing_sub.status = "active"
                        existing_sub.type = subscription_type
                        existing_sub.starts_at = current_time
                        result_sub = existing_sub
                        action = "renewed"
                    else:
                        new_sub = Subscription(
                            user_id=user.id,
                            type=subscription_type,
                            status="active",
                            starts_at=current_time,
                            expires_at=new_expires_at
                        )
                        session.add(new_sub)
                        result_sub = new_sub
                        action = "created"

                    if subscription_type == "premium":
                        user.daily_token_limit = 49999

                logging.info(f"Subscription {action} for user {telegram_id}, expires at {result_sub.expires_at}")
                return result_sub
            except Exception as e:
                logging.error(f"Error creating/extending subscription: {e}")
                return None


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