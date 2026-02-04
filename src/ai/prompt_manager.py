import tiktoken
from .api_client import client
from src.database.CRUDs.user import AsyncUserService
from src.database.CRUDs.dialogue import AsyncDialogueService

async def standard_request(telegram_id: int, user_message: str):
    """
    Args:
        telegram_id: ID пользователя в Telegram
        user_message: Сообщение пользователя

    Returns:
        Ответ ассистента
    """
    try:
        dialogue_user = await AsyncDialogueService.add_message(
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

    conversation_history = await AsyncDialogueService.get_conversation_history(telegram_id, limit=20)
    print(f"Полученная история: {conversation_history}")

    messages_for_api = []
    total_tokens = 0
    if conversation_history:
        try:
            encoding = tiktoken.encoding_for_model("deepseek-chat")
        except:
            encoding = tiktoken.get_encoding("cl100k_base")

        def count_tokens(text):
            return len(encoding.encode(text))

        max_dialog_tokens = 1024
        current_tokens = 0
        recent_history = conversation_history[-15:]
        for msg in reversed(recent_history):
            msg_tokens = count_tokens(msg['content']) + 5
            if current_tokens + msg_tokens <= max_dialog_tokens:
                current_tokens += msg_tokens
                messages_for_api.insert(0, {
                    "role": msg["role"],
                    "content": msg["content"]
                })
    else:
        messages_for_api.append({
            "role": "user",
            "content": user_message
        })
    messages_for_api.insert(0, {"role": "system", "content": "Ты полезный ассистент. Отвечай кратко \
и по делу. Если нужно дать развернутый ответ, ОБЯЗАТЕЛЬНО укладываться в 3000 символов. \
Избегай чрезмерно длинных ответов."})

    print(f"Сообщения для API: {messages_for_api}")

    if not messages_for_api:
        return "Ошибка: пустой диалог"

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages_for_api,
            stream=False,
            max_tokens=2048
        )

        assistant_reply = response.choices[0].message.content
        total_tokens += current_tokens + count_tokens(assistant_reply)

        await AsyncUserService.add_tokens_used(
            telegram_id=telegram_id,
            tokens_used=total_tokens
        )

        await AsyncDialogueService.add_message(
            telegram_id=telegram_id,
            role="assistant",
            content=assistant_reply
        )

        return assistant_reply

    except Exception as e:
        print(f"API error: {e}")
        return "Произошла ошибка при обращении к AI. Попробуйте позже."