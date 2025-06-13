from security import encrypt_data
from config import ENCRYPTION_KEY
from database import save_interaction
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

async def encrypt_api_keys():
    """Шифрування всіх API-ключів."""
    keys = {
        "BINANCE_API_KEY": os.getenv("BINANCE_API_KEY"),
        "BINANCE_API_SECRET": os.getenv("BINANCE_API_SECRET"),
        "BINANCE_TESTNET_API_KEY": os.getenv("BINANCE_TESTNET_API_KEY"),
        "BINANCE_TESTNET_API_SECRET": os.getenv("BINANCE_TESTNET_API_SECRET"),
        "XAI_API_KEY": os.getenv("XAI_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "LLAMA_API_KEY": os.getenv("LLAMA_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY"),
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
        "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN")
    }
    encrypted_keys = {}
    for key_name, key_value in keys.items():
        if key_value:
            encrypted = encrypt_data(key_value)
            encrypted_keys[key_name] = encrypted
            logger.info(f"Encrypted: {key_name}")
            await save_interaction("system", f"Encrypt key: {key_name}", f"Encrypted: {encrypted}")
        else:
            logger.warning(f"{key_name} not found in .env")
    return encrypted_keys

if __name__ == "__main__":
    asyncio.run(encrypt_api_keys())