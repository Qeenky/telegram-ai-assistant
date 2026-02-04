from aiogram.filters import Command
from aiogram import types, Router
from src.database.CRUDs.subscription import AsyncSubscriptionService
from src.database.CRUDs.user import AsyncUserService

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
    active_sub = await AsyncSubscriptionService.get_active_subscription(message.from_user.id)
    text = "Привилегии: "
    if active_sub:
        text += active_sub.type + "\n\n"
    else:
        text += "free\n\n"
    can_chat, temp_text = await AsyncUserService.check_limit_tokens(message.from_user.id)
    text += temp_text
    await message.answer(text)
