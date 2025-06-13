import asyncio
import subprocess
import sys
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

async def install_library(library_name):
    """Асинхронне встановлення бібліотеки через pip."""
    try:
        logger.info(f"Спроба встановити бібліотеку: {library_name}")
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "install", library_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            result = f"Бібліотека {library_name} успішно встановлена"
            logger.info(result)
            await save_interaction("system", f"install_library: {library_name}", result)
            await notify_user("system", result)
            return True
        error = stderr.decode()
        logger.error(f"Помилка встановлення бібліотеки {library_name}: {error}")
        await save_interaction("system", f"install_library: {library_name}", error)
        return False
    except Exception as e:
        logger.error(f"Невідома помилка при встановленні бібліотеки {library_name}: {str(e)}")
        await save_interaction("system", f"install_library: {library_name}", str(e))
        return False

async def check_library_version(library_name):
    """Перевірка версії бібліотеки."""
    try:
        import importlib.metadata
        version = importlib.metadata.version(library_name)
        result = f"{library_name}: версія {version}"
        logger.info(result)
        await save_interaction("system", f"check_version: {library_name}", result)
        return result
    except Exception as e:
        logger.error(f"Помилка перевірки версії {library_name}: {str(e)}")
        return f"Помилка: {str(e)}"