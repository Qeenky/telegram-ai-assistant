from aiogram.filters import Command
from aiogram import types, Router
from src.database.crud import SubscriptionsCRUD
from src.database.crud import check_limit_tokens
from src.database.CRUDs.user import AsyncUserService
from src.database.CRUDs.context_manager import get_db

user_router = Router()

@user_router.message(Command("start"))
async def cmd_start(message: types.Message):
    user, created = await AsyncUserService.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    if created:
        await message.answer(f"Добро пожаловать, {message.from_user.first_name}! Вы успешно зарегистрированы.")
    else:
        await message.answer(f"С возвращением, {message.from_user.first_name}! Рады снова вас видеть.")


# TODO: Обновлять содержание по мере создания функций
@user_router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Помощь\n"+"="*30+"\n\n"+"Команды:\n/limit - проверить лимит токенов.\n/buy - купить premium.")

@user_router.message(Command("limit"))
async def cmd_limit(message: types.Message):
    async with get_db() as db:
        active_sub = await SubscriptionsCRUD.get_active_subscription(message.from_user.id)
        text = "Привилегии: "
        if active_sub:
            text += active_sub.type + "\n\n"
        else:
            text += "free\n\n"

        text += await check_limit_tokens(db, message.from_user.id)
        await message.answer(text)
