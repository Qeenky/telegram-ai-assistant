from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import logging

from src.payments.payment_manager import PaymentManager

logger = logging.getLogger(__name__)

payment_router = Router()


@payment_router.message(Command("buy"))
async def buy_premium_handler(message: Message):
    telegram_id = message.from_user.id

    SUBSCRIPTIONS = {
        "premium_30": {"amount": 299.00, "days": 30, "description": "Премиум подписка"},
        "premium_90": {"amount": 699.00, "days": 90, "description": "Премиум подписка на 3 месяца"},
        "premium_365": {"amount": 1999.00, "days": 365, "description": "Премиум подписка на год"},
    }

    subscription = SUBSCRIPTIONS["premium_30"]

    payment_data = await PaymentManager.create_payment(
        telegram_id=telegram_id,
        amount=subscription["amount"],
        days=subscription["days"],
        description=subscription["description"]
    )

    if not payment_data:
        await message.answer("❌ Ошибка создания платежа. Попробуйте позже.")
        return


    keyboard = PaymentManager.create_payment_keyboard(
        payment_url=payment_data["payment_url"]
    )

    await message.answer(
        f"💳 *Оплата premium подписки*\n\n"
        f"• Сумма: {subscription['amount']} руб.\n"
        f"• Срок: {subscription['days']} дней\n\n"
        f"1. Нажмите кнопку '💳 Оплатить'\n"
        f"2. Оплатите платеж\n"
        f"3. Ожидайте 1-2 минуты\n"
        f"Если возникнут проблемы с оплатой или получением подписки, пишите в поддержку.\n"
        ,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


    await PaymentManager.start_background_check(
        payment_id=payment_data["payment_id"],
        telegram_id=telegram_id,
        timeout_minutes=5
    )


