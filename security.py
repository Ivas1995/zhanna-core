from cryptography.fernet import Fernet
import logging
import os
from config import BASE_DIR, ENCRYPTION_KEY
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

async def encrypt_data(data, user_id="system"):
    """Шифрування даних."""
    try:
        f = Fernet(ENCRYPTION_KEY)
        if isinstance(data, str):
            data = data.encode()
        encrypted = f.encrypt(data)
        result = encrypted.decode()
        await notify_user(user_id, f"Дані зашифровано для user_id: {user_id}")
        return result
    except Exception as e:
        logger.error(f"Помилка шифрування: {str(e)}")
        await notify_user(user_id, f"Помилка шифрування: {str(e)}")
        return data

async def decrypt_data(data, key=None, user_id="system"):
    """Дешифрування даних."""
    try:
        f = Fernet(key or ENCRYPTION_KEY)
        if isinstance(data, str):
            data = data.encode()
        decrypted = f.decrypt(data)
        result = decrypted.decode()
        await notify_user(user_id, f"Дані розшифровано для user_id: {user_id}")
        return result
    except Exception as e:
        logger.error(f"Помилка дешифрування: {str(e)}")
        await notify_user(user_id, f"Помилка дешифрування: {str(e)}")
        return data