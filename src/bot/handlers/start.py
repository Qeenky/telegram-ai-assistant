from aiogram.filters import Command
from aiogram import types, Router



user_router = Router()

@user_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет!")

# TODO: Обновлять содержание по мере создания функций
@user_router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Помощь\n"+"="*30+"\n\n"+"Команды:")