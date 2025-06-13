import httpx
import asyncio
import logging
import os
from config import BASE_DIR, XAI_API_KEY, ENCRYPTION_KEY
from security import decrypt_data
from database import save_cached_response, get_cached_response, save_interaction
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

async def request_xai(prompt, mode="default"):
    """Запит до xAI API."""
    cached_key = f"xai_{prompt}_{mode}"
    cached = await get_cached_response(cached_key)
    if cached:
        return cached
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {decrypt_data(XAI_API_KEY, ENCRYPTION_KEY)}",
                "Content-Type": "application/json"
            }
            data = {
                "prompt": prompt,
                "max_tokens": 500,
                "mode": mode  # default, deepsearch, voice
            }
            response = await client.post("https://api.x.ai/v1/completions", headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json().get("choices")[0].get("text")
                await save_cached_response(cached_key, result)
                await save_interaction("system", f"xAI request: {prompt}", result)
                return result
            return None
    except Exception as e:
        logger.error(f"xAI request error: {str(e)}")
        from self_improvement import handle_error
        await handle_error(str(e))
        return None