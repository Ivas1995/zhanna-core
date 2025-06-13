import os
import subprocess
import logging
from config import BASE_DIR

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_exe():
    """Створення .exe файлу з ізольованим середовищем."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        cmd = [
            "pyinstaller",
            "--onefile",
            "--noconsole",
            "--add-data", f"{os.path.join(BASE_DIR, 'models')};models",
            "--add-data", f"{os.path.join(BASE_DIR, 'templates')};templates",
            "--add-data", f"{os.path.join(BASE_DIR, 'static')};static",
            "--add-data", f"{os.path.join(BASE_DIR, 'plugins')};plugins",
            "--icon", os.path.join(BASE_DIR, "icon.ico") if os.path.exists(os.path.join(BASE_DIR, "icon.ico")) else None,
            "--name", "SakuraAI",
            "--uac-admin",  # Запуск без вимоги адмін-прав
            os.path.join(BASE_DIR, "main.py")
        ]
        cmd = [c for c in cmd if c is not None]
        subprocess.check_call(cmd)
        logger.info("Executable created successfully at dist/SakuraAI.exe")
        print("Executable created successfully at dist/SakuraAI.exe")
    except Exception as e:
        logger.error(f"Error creating executable: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    create_exe()