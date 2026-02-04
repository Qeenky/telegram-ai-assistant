from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from src.config import _Config
from src.database.CRUDs.subscription import AsyncSubscriptionService
user_router = Router()

async def is_admin(telegram_id: int) -> bool:
    return int(_Config.ADMIN_ID) == int(telegram_id)


@user_router.message(Command("grant_premium"))
async def grant_premium(message: Message, days: int = 30):
    if not await is_admin(message.from_user.id):
        return
    text = message.text.split()
    target_user_id = int(text[1]) #/grant_premium target_id days
    if len(text) >= 3:
        days = int(text[2])

    await AsyncSubscriptionService.create_subscription(target_user_id, "premium", days)
    await message.answer(f"✅ Подписка выдана на {days} дней")
