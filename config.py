import os
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class Config(BaseModel):
    BASE_DIR: str
    MODEL_NAME: str
    MODEL_PATH: str
    MEDIA_DIR: str
    BACKUP_DIR: str
    UPDATE_DIR: str
    TELEGRAM_TOKEN: str
    GITHUB_TOKEN: str
    XAI_API_KEY: str
    OPENAI_API_KEY: str
    LLAMA_API_KEY: str
    GOOGLE_API_KEY: str
    GOOGLE_CSE_ID: str
    YOUTUBE_API_KEY: str
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    BINANCE_TESTNET_API_KEY: str
    BINANCE_TESTNET_API_SECRET: str
    ENCRYPTION_KEY: bytes
    TTS_ENABLED: bool
    TTS_LANGUAGE: str
    TTS_ENGINE: str
    VOSK_MODEL_PATH: str
    LOG_FILE: str
    DB_TYPE: str
    DB_PATH: str
    POSTGRES_URL: str
    ENVIRONMENT: str = "development"

    class Config:
        arbitrary_types_allowed = True

def validate_config():
    try:
        config_data = {
            "BASE_DIR": os.getenv("BASE_DIR", r"C:\Zhanna\startup"),
            "MODEL_NAME": os.getenv("MODEL_NAME", "mistral-7b-openorca.Q4_0.gguf"),
            "MODEL_PATH": os.path.join(os.getenv("BASE_DIR", r"C:\Zhanna\startup"), "models"),
            "MEDIA_DIR": os.path.join(os.getenv("BASE_DIR", r"C:\Zhanna\startup"), "media"),
            "BACKUP_DIR": os.path.join(os.getenv("BASE_DIR", r"C:\Zhanna\startup"), "backups"),
            "UPDATE_DIR": os.path.join(os.getenv("BASE_DIR", r"C:\Zhanna\startup"), "updates"),
            "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN"),
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
            "XAI_API_KEY": os.getenv("XAI_API_KEY"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "LLAMA_API_KEY": os.getenv("LLAMA_API_KEY"),
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
            "GOOGLE_CSE_ID": os.getenv("GOOGLE_CSE_ID"),
            "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY"),
            "BINANCE_API_KEY": os.getenv("BINANCE_API_KEY"),
            "BINANCE_API_SECRET": os.getenv("BINANCE_API_SECRET"),
            "BINANCE_TESTNET_API_KEY": os.getenv("BINANCE_TESTNET_API_KEY"),
            "BINANCE_TESTNET_API_SECRET": os.getenv("BINANCE_TESTNET_API_SECRET"),
            "TTS_ENABLED": os.getenv("TTS_ENABLED", "True").lower() == "true",
            "TTS_LANGUAGE": os.getenv("TTS_LANGUAGE", "uk-UA"),
            "TTS_ENGINE": os.getenv("TTS_ENGINE", "pyttsx3"),
            "VOSK_MODEL_PATH": os.path.join(os.getenv("BASE_DIR", r"C:\Zhanna\startup"), "models", "vosk-model-uk"),
            "LOG_FILE": os.path.join(os.getenv("BASE_DIR", r"C:\Zhanna\startup"), "sakura.log"),
            "DB_TYPE": os.getenv("DB_TYPE", "sqlite"),
            "DB_PATH": os.path.join(os.getenv("BASE_DIR", r"C:\Zhanna\startup"), "data", "sakura_history.db"),
            "POSTGRES_URL": os.getenv("POSTGRES_URL", "postgresql://user:pass@localhost/sakura"),
            "ENCRYPTION_KEY": None  # Will be derived
        }
        # Derive encryption key
        SALT = b"sakura_salt_v2"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SALT,
            iterations=100000,
        )
        config_data["ENCRYPTION_KEY"] = base64.urlsafe_b64encode(kdf.derive(os.getenv("ENCRYPTION_KEY", "1234567890abcdef1234567890abcdef").encode()))
        return Config(**config_data)
    except ValidationError as e:
        logger.error(f"Configuration validation error: {str(e)}")
        raise

CONFIG = validate_config()