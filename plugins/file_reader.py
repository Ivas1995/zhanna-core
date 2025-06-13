import aiofiles
import asyncio
import logging
import os
from config import BASE_DIR
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

async def read_file(file_path, user_id):
    """Асинхронне читання файлу."""
    try:
        if not os.path.exists(file_path):
            return f"Файл {file_path} не знайдено"
        if not file_path.startswith(BASE_DIR):
            file_path = os.path.join(BASE_DIR, file_path)
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
        result = f"Вміст файлу {file_path}:\n{content[:1000]}"  # Обмеження для Telegram
        await notify_user(user_id, result)
        await save_interaction(user_id, f"read_file: {file_path}", result)
        return result
    except UnicodeDecodeError:
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
        result = f"Бінарний файл {file_path}: {content[:100].hex()}"
        await notify_user(user_id, result)
        await save_interaction(user_id, f"read_binary: {file_path}", result)
        return result
    except Exception as e:
        logger.error(f"File read error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка читання файлу: {str(e)}"