from aiogram.filters import Command
from aiogram import types, Router



user_router = Router()

@user_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет!")