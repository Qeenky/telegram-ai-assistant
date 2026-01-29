import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")



class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Ошибка: TELEGRAM_BOT_TOKEN не найден в .env файле!")
    if not DEEPSEEK_API_KEY:
        raise ValueError("<Ошибка>: DEEPSEEK_API_KEY не найден в .env файле!")



# Создаём глобальный объект настроек
_Config = Config()
