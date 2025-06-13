import asyncio
import logging
import os
import ast
from config import BASE_DIR, OPENAI_API_KEY, LLAMA_API_KEY, ENCRYPTION_KEY
from database import save_upgrade, save_interaction
from security import decrypt_data
from utils.notify_user import notify_user
from openai import request_openai
import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def init_zhanna_connection():
    """Ініціалізація Zhanna."""
    from utils.network import is_online
    if not await is_online():
        logger.warning("Офлайн режим, Zhanna недоступна")
        return
    try:
        response = await request_openai("Перевірка зв'язку з Zhanna")
        if response:
            logger.info("Zhanna ініціалізовано")
    except Exception as e:
        logger.error(f"Zhanna init error: {str(e)}")

async def request_llama_upgrade(prompt):
    """Запит до LLaMA API для оновлення коду."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.llama.ai/v1/completions",
                headers={"Authorization": f"Bearer {decrypt_data(LLAMA_API_KEY)}"},
                json={"prompt": prompt, "max_tokens": 500},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("choices")[0].get("text")
            return None
    except Exception as e:
        logger.error(f"LLaMA error: {str(e)}")
        return None

async def validate_code(code):
    """Перевірка синтаксису коду."""
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logger.error(f"Некоректний код: {str(e)}")
        return False

async def request_zhanna_upgrade(user_id, command):
    """Запит на оновлення через Zhanna."""
    try:
        from utils.network import is_online
        if not await is_online():
            from gpt4all import GPT4All
            model = GPT4All("mistral-7b-openorca.Q4_0.gguf", model_path=os.path.join(BASE_DIR, "models"))
            response = model.generate(f"Оновити код для: {command}", max_tokens=500)
            if await validate_code(response):
                with open(os.path.join(BASE_DIR, "updates", "zhanna_update.py"), "w", encoding="utf-8") as f:
                    f.write(response)
                await save_upgrade(user_id, command, "local_mistral", "completed")
                await notify_user(user_id, "Оновлення збережено локально (Mistral)")
                return response
            return "Некоректний код від локальної моделі"
        prompt = f"Оновити код для команди: {command}"
        response = await request_openai(prompt)
        if not response:
            response = await request_llama_upgrade(prompt)
        if response and await validate_code(response):
            with open(os.path.join(BASE_DIR, "updates", "zhanna_update.py"), "w", encoding="utf-8") as f:
                f.write(response)
            await save_upgrade(user_id, command, "openai" if response else "llama", "completed")
            await notify_user(user_id, f"Оновлення збережено: {response[:100]}...")
            await save_interaction(user_id, f"Zhanna upgrade: {command}", response)
            return response
        return "Некоректний код від Zhanna"
    except Exception as e:
        logger.error(f"Zhanna upgrade error: {str(e)}")
        from self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка оновлення: {str(e)}"