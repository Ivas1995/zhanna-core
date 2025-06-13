import httpx
import asyncio
import logging
import os
import webbrowser
from config import BASE_DIR, YOUTUBE_API_KEY, ENCRYPTION_KEY
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

async def search_youtube(query):
    """Пошук відео на YouTube."""
    cached_key = f"youtube_{query}"
    cached = await get_cached_response(cached_key)
    if cached:
        return cached
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={decrypt_data(YOUTUBE_API_KEY, ENCRYPTION_KEY)}"
            response = await client.get(url, timeout=10)
            if response.status_code == 200:
                videos = response.json().get("items", [])[:1]
                if videos:
                    video_id = videos[0]["id"]["videoId"]
                    result = f"https://www.youtube.com/watch?v={video_id}"
                    await save_cached_response(cached_key, result)
                    return result
                return "Відео не знайдено"
            return "Помилка пошуку на YouTube"
    except Exception as e:
        logger.error(f"YouTube search error: {str(e)}")
        return f"Помилка: {str(e)}"

async def play_youtube(query, user_id):
    """Відтворення відео або локального медіа."""
    try:
        from utils.network import is_online
        if not await is_online():
            # Офлайн: пошук локальних медіа
            media_dir = os.path.join(BASE_DIR, "media")
            for file in glob.glob(os.path.join(media_dir, "*.mp3")):
                if query.lower() in file.lower():
                    os.startfile(file)
                    result = f"Відтворюється локальний файл: {file}"
                    await notify_user(user_id, result)
                    await save_interaction(user_id, f"play_local: {query}", result)
                    return result
            return "Локальні медіа не знайдено"
        video_url = await search_youtube(query)
        if "Помилка" not in video_url:
            webbrowser.open(video_url)
            result = f"Відтворюється: {video_url}"
            await notify_user(user_id, result)
            await save_interaction(user_id, f"play_youtube: {query}", result)
            return result
        return video_url
    except Exception as e:
        logger.error(f"YouTube play error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка відтворення: {str(e)}"