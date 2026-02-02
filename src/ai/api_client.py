from openai import OpenAI
from src.config import _Config

client = OpenAI(
    api_key=_Config.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)