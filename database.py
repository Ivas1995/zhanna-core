import sqlite3
import asyncio
import logging
import os
from config import BASE_DIR, DB_PATH, DB_TYPE, POSTGRES_URL
import asyncpg
from security import encrypt_data, decrypt_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def init_db():
    """Ініціалізація бази даних."""
    try:
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    query TEXT,
                    response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS context (
                    user_id TEXT PRIMARY KEY,
                    context_data TEXT
                );
                CREATE TABLE IF NOT EXISTS cache (
                    query_hash TEXT PRIMARY KEY,
                    response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS suspicious_processes (
                    id SERIAL PRIMARY KEY,
                    process_name TEXT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    path TEXT,
                    status TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    symbol TEXT,
                    side TEXT,
                    quantity REAL,
                    price REAL,
                    status TEXT,
                    is_testnet BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS upgrades (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    upgrade_request TEXT,
                    status TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS instructions (
                    id SERIAL PRIMARY KEY,
                    query TEXT,
                    response TEXT,
                    source TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            await conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    query TEXT,
                    response TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS context (
                    user_id TEXT PRIMARY KEY,
                    context_data TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    query_hash TEXT PRIMARY KEY,
                    response TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS suspicious_processes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    path TEXT,
                    status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    symbol TEXT,
                    side TEXT,
                    quantity REAL,
                    price REAL,
                    status TEXT,
                    is_testnet BOOLEAN,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS upgrades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    upgrade_request TEXT,
                    status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS instructions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    response TEXT,
                    source TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        logger.info("База даних ініціалізована")
    except Exception as e:
        logger.error(f"Помилка ініціалізації бази даних: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))

async def save_interaction(user_id, query, response):
    """Збереження взаємодії в базі даних."""
    try:
        encrypted_response = await encrypt_data(response, user_id)
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            await conn.execute(
                "INSERT INTO history (user_id, query, response) VALUES ($1, $2, $3)",
                user_id, query, encrypted_response
            )
            await conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO history (user_id, query, response) VALUES (?, ?, ?)",
                (user_id, query, encrypted_response)
            )
            conn.commit()
            conn.close()
        logger.info(f"Взаємодія збережена для user_id: {user_id}")
    except Exception as e:
        logger.error(f"Помилка збереження взаємодії: {str(e)}")

async def get_context(user_id):
    """Отримання контексту користувача."""
    try:
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            result = await conn.fetchrow("SELECT context_data FROM context WHERE user_id = $1", user_id)
            await conn.close()
            if result:
                return await decrypt_data(result['context_data'], user_id=user_id)
            return ""
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT context_data FROM context WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            conn.close()
            if result:
                return await decrypt_data(result[0], user_id=user_id)
            return ""
    except Exception as e:
        logger.error(f"Помилка отримання контексту: {str(e)}")
        return ""

async def save_context(user_id, context_data):
    """Збереження контексту користувача."""
    try:
        encrypted_context = await encrypt_data(context_data, user_id)
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            await conn.execute(
                "INSERT INTO context (user_id, context_data) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET context_data = $2",
                user_id, encrypted_context
            )
            await conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO context (user_id, context_data) VALUES (?, ?)",
                (user_id, encrypted_context)
            )
            conn.commit()
            conn.close()
        logger.info(f"Контекст збережено для user_id: {user_id}")
    except Exception as e:
        logger.error(f"Помилка збереження контексту: {str(e)}")

async def get_cached_response(query_hash):
    """Отримання кешованої відповіді."""
    try:
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            result = await conn.fetchrow("SELECT response FROM cache WHERE query_hash = $1", query_hash)
            await conn.close()
            if result:
                return await decrypt_data(result['response'])
            return None
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT response FROM cache WHERE query_hash = ?", (query_hash,))
            result = c.fetchone()
            conn.close()
            if result:
                return await decrypt_data(result[0])
            return None
    except Exception as e:
        logger.error(f"Помилка отримання кешованої відповіді: {str(e)}")
        return None

async def save_cached_response(query_hash, response):
    """Збереження кешованої відповіді."""
    try:
        encrypted_response = await encrypt_data(response)
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            await conn.execute(
                "INSERT INTO cache (query_hash, response) VALUES ($1, $2) ON CONFLICT (query_hash) DO UPDATE SET response = $2",
                query_hash, encrypted_response
            )
            await conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO cache (query_hash, response) VALUES (?, ?)",
                (query_hash, encrypted_response)
            )
            conn.commit()
            conn.close()
        logger.info(f"Кешована відповідь збережена для: {query_hash}")
    except Exception as e:
        logger.error(f"Помилка збереження кешованої відповіді: {str(e)}")

async def save_suspicious_process(process_info):
    """Збереження інформації про підозрілий процес."""
    try:
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            await conn.execute(
                "INSERT INTO suspicious_processes (process_name, cpu_percent, memory_percent, path, status) VALUES ($1, $2, $3, $4, $5)",
                process_info['name'], process_info['cpu_percent'], process_info['memory_percent'], process_info['path'], process_info['status']
            )
            await conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO suspicious_processes (process_name, cpu_percent, memory_percent, path, status) VALUES (?, ?, ?, ?, ?)",
                (process_info['name'], process_info['cpu_percent'], process_info['memory_percent'], process_info['path'], process_info['status'])
            )
            conn.commit()
            conn.close()
        logger.info(f"Підозрілий процес збережено: {process_info['name']}")
    except Exception as e:
        logger.error(f"Помилка збереження підозрілого процесу: {str(e)}")

async def save_trade(trade_info):
    """Збереження торговельної угоди."""
    try:
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            await conn.execute(
                "INSERT INTO trades (user_id, symbol, side, quantity, price, status, is_testnet) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                trade_info['user_id'], trade_info['symbol'], trade_info['side'], trade_info['quantity'],
                trade_info['price'], trade_info['status'], trade_info['is_testnet']
            )
            await conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO trades (user_id, symbol, side, quantity, price, status, is_testnet) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (trade_info['user_id'], trade_info['symbol'], trade_info['side'], trade_info['quantity'],
                 trade_info['price'], trade_info['status'], trade_info['is_testnet'])
            )
            conn.commit()
            conn.close()
        logger.info(f"Угода збережена: {trade_info['symbol']}")
    except Exception as e:
        logger.error(f"Помилка збереження угоди: {str(e)}")

async def save_upgrade(user_id, upgrade_request, source, status):
    """Збереження запиту на оновлення."""
    try:
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            await conn.execute(
                "INSERT INTO upgrades (user_id, upgrade_request, status) VALUES ($1, $2, $3)",
                user_id, upgrade_request, status
            )
            await conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO upgrades (user_id, upgrade_request, status) VALUES (?, ?, ?)",
                (user_id, upgrade_request, status)
            )
            conn.commit()
            conn.close()
        logger.info(f"Оновлення збережено для user_id: {user_id}, джерело: {source}")
    except Exception as e:
        logger.error(f"Помилка збереження оновлення: {str(e)}")

async def save_instruction(query, response, source):
    """Збереження інструкції."""
    try:
        encrypted_response = await encrypt_data(response)
        if DB_TYPE == "postgresql":
            conn = await asyncpg.connect(POSTGRES_URL)
            await conn.execute(
                "INSERT INTO instructions (query, response, source) VALUES ($1, $2, $3)",
                query, encrypted_response, source
            )
            await conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO instructions (query, response, source) VALUES (?, ?, ?)",
                (query, encrypted_response, source)
            )
            conn.commit()
            conn.close()
        logger.info(f"Інструкція збережена для запиту: {query}")
    except Exception as e:
        logger.error(f"Помилка збереження інструкції: {str(e)}")