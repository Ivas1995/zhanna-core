import httpx
import asyncio
import logging
import os
from config import BASE_DIR, GOOGLE_API_KEY, GOOGLE_CSE_ID
from database import save_cached_response, get_cached_response, save_interaction
from utils.notify_user import notify_user
from main import request_xai_instruction

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def search_x_platform(query):
    """Пошук через X API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.x.com/search?q={query}", timeout=10)
            if response.status_code == 200:
                results = response.json().get("posts", [])[:3]
                return "\n".join([f"{r.get('title', 'No Title')}: {r.get('url', 'No URL')}" for r in results])
            return "Немає результатів з X."
    except Exception as e:
        logger.error(f"X search error: {str(e)}")
        return f"Помилка пошуку на X: {str(e)}"

async def search_google(query):
    """Пошук через Google CSE."""
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={query}"
            response = await client.get(url, timeout=10)
            if response.status_code == 200:
                results = response.json().get("items", [])[:3]
                return "\n".join([f"{r['title']}: {r['link']}" for r in results])
            return "Немає результатів з Google."
    except Exception as e:
        logger.error(f"Google search error: {str(e)}")
        return f"Помилка пошуку Google: {str(e)}"

async def search_query(query, user_id):
    """Основна функція пошуку."""
    if not query:
        return "Вкажіть запит для пошуку!"
    cached_key = f"search_{query}"
    cached = await get_cached_response(cached_key)
    if cached:
        await notify_user(user_id, f"Кешовано: {cached}")
        return cached
    try:
        x_results = await search_x_platform(query)
        google_results = await search_google(query)
        result_text = f"Результати з X:\n{x_results}\n\nРезультати з Google:\n{google_results}"
        analysis = await request_xai_instruction(f"Узагальни результати пошуку: {result_text}", mode="deepsearch")
        if analysis:
            result_text += f"\n\nАналіз (Grok 3): {analysis}"
        await save_cached_response(cached_key, result_text)
        await save_interaction(user_id, f"Search: {query}", result_text)
        await notify_user(user_id, result_text)
        return result_text
    except Exception as e:
        logger.error(f"Search query error: {str(e)}")
        from self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка пошуку: {str(e)}"