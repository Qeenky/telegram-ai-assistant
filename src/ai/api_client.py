from openai import OpenAI
from src.config import _Config

client = OpenAI(
    api_key=_Config.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# TODO Реализловать подгрузку истории из бд и загрузку обновленной истории
def standard_request(user_message, conversation_history):
    conversation_history.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="deepseek-chat", messages=conversation_history,
        stream=False, max_tokens=4096
    )
    assistant_reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return conversation_history, assistant_reply