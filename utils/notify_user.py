import httpx
import asyncio
import logging
import os
from config import BASE_DIR, TELEGRAM_TOKEN
from utils.network import is_online

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
    """Надсилання повідомлення користувачу через Telegram або GUI."""
    try:
        if await is_online() and TELEGRAM_TOKEN:
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                data = {
                    "chat_id": user_id,
                    "text": message[:4096],  # Telegram обмеження
                    "parse_mode": "Markdown"
                }
                response = await client.post(url, json=data, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Повідомлення надіслано до {user_id}: {message[:100]}...")
                    # Збереження взаємодії перенесено в викликаючий код, щоб уникнути циклічних імпортів
                    return True
                logger.error(f"Помилка Telegram API: {response.text}")
        # Fallback: Логування в файл
        logger.info(f"Офлайн повідомлення для {user_id}: {message}")
        # Спроба через GUI (якщо активний)
        try:
            from gui import SakuraGUI
            gui = SakuraGUI.instance()  # Припускаємо, що GUI має синглтон
            if gui:
                gui.add_message(f"Сакура: {message}")
        except Exception:
            pass
        return False
    except Exception as e:
        logger.error(f"Помилка сповіщення: {str(e)}")
        return False