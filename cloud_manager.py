import asyncio
import logging
import os
import shutil
from datetime import datetime
from config import BASE_DIR, BACKUP_DIR
from utils import notify_user
from database import save_interaction
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def create_backup(user_id):
    """Створення локального бекапу."""
    try:
        backup_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        os.makedirs(backup_path, exist_ok=True)
        shutil.copy(os.path.join(BASE_DIR, "data", "sakura_history.db"), backup_path)
        for file in glob.glob(os.path.join(BASE_DIR, "*.py")):
            shutil.copy(file, backup_path)
        result = f"Бекап створено: {backup_path}"
        await notify_user(user_id, result)
        await save_interaction(user_id, "create_backup", result)
        return backup_path
    except Exception as e:
        logger.error(f"Backup creation error: {str(e)}")
        return f"Помилка створення бекапу: {str(e)}"

async def upload_to_drive(file_path, user_id):
    """Завантаження бекапу на Google Drive."""
    try:
        creds = Credentials.from_authorized_user_file(os.path.join(BASE_DIR, "token.json"))
        service = build("drive", "v3", credentials=creds)
        file_metadata = {"name": os.path.basename(file_path)}
        media = MediaFileUpload(file_path)
        file = service.files().create(body=file_metadata, media_body=media).execute()
        result = f"Файл завантажено на Google Drive: {file['name']}"
        await notify_user(user_id, result)
        await save_interaction(user_id, "upload_backup", result)
        return result
    except Exception as e:
        logger.error(f"Google Drive upload error: {str(e)}")
        return f"Помилка завантаження: {str(e)}"

async def check_cloud_status(user_id):
    """Перевірка статусу бекапів."""
    try:
        backup_path = BACKUP_DIR
        if os.path.exists(backup_path):
            files = os.listdir(backup_path)
            if files:
                return f"Резервне копіювання: {len(files)} файлів"
            return "Резервне копіювання порожнє"
        return "Резервне копіювання не налаштовано"
    except Exception as e:
        logger.error(f"Cloud status error: {str(e)}")
        return f"Помилка: {str(e)}"

async def start_cloud_manager(user_id):
    """Фоновий менеджер бекапів."""
    while True:
        try:
            backup_path = await create_backup(user_id)
            if "Помилка" not in backup_path:
                await upload_to_drive(backup_path, user_id)
            status = await check_cloud_status(user_id)
            await notify_user(user_id, status)
            await asyncio.sleep(43200)  # 12 годин
        except Exception as e:
            logger.error(f"Cloud manager error: {str(e)}")
            await asyncio.sleep(3600)