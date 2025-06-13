import httpx
import asyncio
import logging
import os
import ast
from config import BASE_DIR, OPENAI_API_KEY, ENCRYPTION_KEY
from security import decrypt_data
from database import save_interaction
from utils.notify_user import notify_user

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def request_openai(prompt):
    """Запит до OpenAI API (gpt-3.5-turbo)."""
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {decrypt_data(OPENAI_API_KEY, ENCRYPTION_KEY)}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            }
            response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"]
                await save_interaction("system", f"OpenAI request: {prompt[:100]}", result)
                return result
            return None
    except Exception as e:
        logger.error(f"OpenAI request error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return None

async def request_gpt_upgrade(prompt):
    """Запит на покращення коду через OpenAI."""
    try:
        code = await request_openai(f"Покращити цей Python код:\n{prompt}")
        if code and ast.parse(code):
            with open(os.path.join(BASE_DIR, "updates", "gpt_update.py"), "w", encoding="utf-8") as f:
                f.write(code)
            return code
        return None
    except Exception as e:
        logger.error(f"GPT upgrade error: {str(e)}")
        return None

async def apply_gpt_upgrade(code):
    """Застосування покращеного коду."""
    try:
        if ast.parse(code):
            with open(os.path.join(BASE_DIR, "updates", "applied_gpt_update.py"), "w", encoding="utf-8") as f:
                f.write(code)
            await notify_user("system", "Покращення від GPT застосовано")
            return True
        return False
    except Exception as e:
        logger.error(f"Apply GPT upgrade error: {str(e)}")
        return False