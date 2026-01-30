from aiogram.filters import Command
from aiogram import types, Router
from src.database.crud import get_db, get_or_create_user


user_router = Router()

@user_router.message(Command("start"))
async def cmd_start(message: types.Message):
    with get_db() as db:
        user, created = get_or_create_user(
            session=db,
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )

        if created:
            await message.answer(f"Добро пожаловать, {message.from_user.first_name}! Вы успешно зарегистрированы.")
        else:
            await message.answer(f"С возвращением, {message.from_user.first_name}! Рады снова вас видеть.")


# TODO: Обновлять содержание по мере создания функций
@user_router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Помощь\n"+"="*30+"\n\n"+"Команды:")