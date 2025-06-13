import httpx
import asyncio
import logging
import os
from config import BASE_DIR
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

async def is_online():
    """Перевірка доступу до інтернету."""
    endpoints = ["https://www.google.com", "https://api.x.com/ping"]
    for url in endpoints:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5)
                if response.status_code == 200:
                    return True
        except Exception:
            continue
    logger.warning("No internet connection detected.")
    return False

async def ping_endpoint(endpoint):
    """Асинхронний пінг ендпоінту."""
    try:
        async with httpx.AsyncClient() as client:
            start = asyncio.get_event_loop().time()
            response = await client.get(endpoint, timeout=5)
            latency = (asyncio.get_event_loop().time() - start) * 1000
            if response.status_code == 200:
                return f"{endpoint}: OK (Латентність: {latency:.2f} мс)"
            return f"{endpoint}: Помилка ({response.status_code})"
    except Exception as e:
        return f"{endpoint}: Помилка ({str(e)})"

async def check_network_status(user_id):
    """Перевірка статусу мережі."""
    try:
        results = await asyncio.gather(
            ping_endpoint("https://www.google.com"),
            ping_endpoint("https://api.x.com/ping"),
            ping_endpoint("https://api.binance.com/api/v3/ping")
        )
        result_text = "\n".join(results)
        await notify_user(user_id, result_text)
        return result_text
    except Exception as e:
        logger.error(f"Network status error: {str(e)}")
        error_message = f"Помилка перевірки мережі: {str(e)}"
        await notify_user(user_id, error_message)
        return error_message