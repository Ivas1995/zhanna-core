import asyncio
import logging
import os
import aiohttp
from config import BASE_DIR, TELEGRAM_TOKEN
from telegram import Bot
from telegram.request import HTTPXRequest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def notify_user(user_id, message):
    """Відправлення повідомлення користувачу через Telegram."""
    try:
        bot = Bot(token=TELEGRAM_TOKEN, request=HTTPXRequest())
        await bot.send_message(chat_id=user_id, text=message)
        logger.info(f"Повідомлення надіслано користувачу {user_id}: {message}")
    except Exception as e:
        logger.error(f"Помилка надсилання повідомлення: {str(e)}")

async def is_online():
    """Перевірка підключення до інтернету."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.google.com", timeout=5) as response:
                return response.status == 200
    except Exception:
        return False