import asyncio
import logging
import os
from config import BASE_DIR
from database import save_instruction, get_cached_response
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

async def learn_response(query, response):
    """Збереження вивченої відповіді."""
    try:
        cached = await get_cached_response(f"learn_{query}")
        if cached:
            logger.info(f"Відповідь для {query} уже збережена")
            return
        analysis = await request_xai_instruction(f"Класифікувати запит: {query}", mode="deepsearch")
        source = "xai" if analysis else "local"
        await save_instruction(query, response, source)
        logger.info(f"Вивчено відповідь для запиту: {query}")
    except Exception as e:
        logger.error(f"Learn response error: {str(e)}")
        from self_improvement import handle_error
        await handle_error(str(e))

async def clean_old_instructions(max_entries=1000):
    """Очищення старих інструкцій."""
    try:
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            await conn.execute("DELETE FROM instructions WHERE id NOT IN (SELECT id FROM instructions ORDER BY timestamp DESC LIMIT $1)", max_entries)
            await conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM instructions WHERE id NOT IN (SELECT id FROM instructions ORDER BY timestamp DESC LIMIT ?)", (max_entries,))
            conn.commit()
            conn.close()
        logger.info(f"Очищено старі інструкції, залишено {max_entries}")
    except Exception as e:
        logger.error(f"Clean instructions error: {str(e)}")