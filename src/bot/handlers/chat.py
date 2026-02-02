from aiogram import Router, F
from aiogram.types import Message
from src.ai.prompt_manager import standard_request
from src.database.crud import get_db, check_tokens_used


user_router = Router()

@user_router.message(F.text & ~F.text.startswith('/'))
async def user_message(message: Message):
    try:
        async with get_db() as session:
            can_chat = await check_tokens_used(session, message.from_user.id)
            if not can_chat:
                return await message.answer("Достигнут лимит токенов.")

            typing_msg = await message.answer("Думаю...")

            response = await standard_request(
                telegram_id=message.from_user.id,
                user_message=message.text
            )

            await typing_msg.delete()
            await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка: {e}")