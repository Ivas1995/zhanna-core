import os
import glob
import aiofiles
import asyncio
import logging
from config import BASE_DIR
from database import save_interaction

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def check_file_encoding(file_path):
    """Асинхронна перевірка кодування файлу."""
    supported_extensions = ('.py', '.txt', '.json', '.css', '.js')
    if not file_path.endswith(supported_extensions):
        logger.info(f"{file_path}: Ignored (unsupported format)")
        return
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            await f.read()
        result = f"{file_path}: UTF-8 OK"
        logger.info(result)
        await save_interaction("system", f"Check encoding: {file_path}", result)
        print(result)
    except UnicodeDecodeError:
        result = f"{file_path}: Некоректне кодування (не UTF-8)"
        logger.error(result)
        await save_interaction("system", f"Check encoding: {file_path}", result)
        print(result)
    except Exception as e:
        result = f"{file_path}: Помилка перевірки: {str(e)}"
        logger.error(result)
        await save_interaction("system", f"Check encoding: {file_path}", result)
        print(result)

async def check_all_files():
    """Перевірка всіх файлів у директорії."""
    async for file in glob.iglob(os.path.join(BASE_DIR, "**/*"), recursive=True):
        if os.path.isfile(file):
            await check_file_encoding(file)

if __name__ == "__main__":
    asyncio.run(check_all_files())