from aiogram import Router, F
from aiogram.types import Message
from src.ai.api_client import standard_request
from src.database.crud import get_db, check_tokens_used
import asyncio

user_router = Router()

@user_router.message(F.text & ~F.text.startswith('/'))
async def user_message(message: Message):
    try:
        with get_db() as db:
            if check_tokens_used(db, message.from_user.id) == False:
                return message.answer("Достигнут лимит токенов.")
            else:
                typing_msg = await message.answer("Думаю...")

                response = await asyncio.to_thread(
                    standard_request,
                    message.from_user.id,
                    message.text
                )

                await typing_msg.delete()
                await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        print(e)