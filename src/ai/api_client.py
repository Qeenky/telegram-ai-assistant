from openai import OpenAI
from src.config import _Config
from src.database.crud import get_db, DialogueCRUD
from contextlib import contextmanager

client = OpenAI(
    api_key=_Config.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

@contextmanager
def get_db_session():
    with get_db() as db:
        yield db


def standard_request(telegram_id: int, user_message: str):
    """
    Args:
        telegram_id: ID пользователя в Telegram
        user_message: Сообщение пользователя

    Returns:
        Ответ ассистента
    """
    with get_db_session() as db:
        try:
            dialogue_user = DialogueCRUD.add_message(
                session=db,
                telegram_id=telegram_id,
                role="user",
                content=user_message
            )
            print(f"После добавления сообщения пользователя: {dialogue_user}")
            print(f"История после добавления пользователя: {dialogue_user.conversation_history}")

        except ValueError:
            return "Пользователь не найден. Пожалуйста, сначала выполните команду /start"
        except Exception as e:
            print(f"Ошибка при добавлении сообщения пользователя: {e}")
            return "Произошла ошибка при сохранении сообщения"

        conversation_history = DialogueCRUD.get_conversation_history(db, telegram_id)
        print(f"Полученная история: {conversation_history}")

        messages_for_api = []

        # TODO: Реализовать ограничение по токенам, вместо сообщений
        if conversation_history:
            recent_history = conversation_history[-19:]
            for msg in recent_history:
                if msg.get("content") and msg.get("role"):
                    messages_for_api.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        else:
            messages_for_api.append({
                "role": "user",
                "content": user_message
            })

        print(f"Сообщения для API: {messages_for_api}")

        if not messages_for_api:
            return "Ошибка: пустой диалог"

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages_for_api,
                stream=False,
                max_tokens=4096
            )

            assistant_reply = response.choices[0].message.content

            DialogueCRUD.add_message(
                session=db,
                telegram_id=telegram_id,
                role="assistant",
                content=assistant_reply
            )

            return assistant_reply

        except Exception as e:
            print(f"API error: {e}")
            return "Произошла ошибка при обращении к AI. Попробуйте позже."