from aiogram import Router, F
from aiogram.types import Message
from src.ai.api_client import standard_request

user_router = Router()

@user_router.message(F.text & ~F.text.startswith('/'))
async def user_message(message: Message):
    try:
        await message.answer(standard_request(message.from_user.id, message.text))
    except Exception as e:
        print(e)