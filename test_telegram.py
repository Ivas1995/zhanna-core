from telegram.ext import Application, JobQueue
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TELEGRAM_TOKEN
import pytz
import logging
import os

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(r"C:\Zhanna\startup", "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    scheduler = AsyncIOScheduler(timezone=pytz.timezone('Europe/Kyiv'))
    job_queue = JobQueue()
    job_queue.scheduler = scheduler
    job_queue.start()
    app = Application.builder().token(TELEGRAM_TOKEN).job_queue(job_queue).build()
    print("Telegram Application ініціалізовано успішно!")
except Exception as e:
    logger.error(f"Помилка ініціалізації Telegram: {str(e)}")
    print(f"Помилка: {str(e)}")