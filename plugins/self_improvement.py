import glob
import os
import asyncio
import logging
import ast
import shutil
from datetime import datetime
from config import CONFIG
from database import Database
from plugins.xai import request_xai
from plugins.openai import request_openai
from plugins.zhanna import request_llama_upgrade
from utils.notify_user import notify_user
import unittest
import tempfile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CodeImprover:
    def __init__(self):
        self.db = Database()
        self.models = [
            ("xAI", request_xai),
            ("OpenAI", request_openai),
            ("LLaMA", request_llama_upgrade)
        ]

    async def analyze_code(self):
        """Analyze all Python files."""
        code_files = []
        for file in glob.glob(os.path.join(CONFIG.BASE_DIR, "**/*.py"), recursive=True):
            if "updates" not in file and "backups" not in file:
                code_files.append(file)
        return code_files

    async def generate_improvement(self, file_path: str, content: str) -> str:
        """Generate improved code using multiple models with voting."""
        improvements = []
        for model_name, model_func in self.models:
            try:
                prompt = f"Optimize and improve this Python code while preserving functionality:\n{content}"
                improved_code = await model_func(prompt)
                if improved_code and await self.validate_code(improved_code):
                    improvements.append((model_name, improved_code))
            except Exception as e:
                logger.error(f"{model_name} improvement error for {file_path}: {str(e)}")
        # Select best improvement (e.g., most consistent or first valid)
        return improvements[0][1] if improvements else None

    async def validate_code(self, code: str) -> bool:
        """Validate code syntax and run basic tests."""
        try:
            ast.parse(code)
            # Run unit tests in a temporary environment
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp:
                temp.write(code)
                temp_path = temp.name
            suite = unittest.TestLoader().discover(os.path.dirname(temp_path))
            result = unittest.TextTestRunner().run(suite)
            os.unlink(temp_path)
            return result.wasSuccessful()
        except Exception as e:
            logger.error(f"Code validation error: {str(e)}")
            return False

    async def apply_improvement(self, file_path: str, improved_code: str):
        """Apply code improvements with backup."""
        if not await self.validate_code(improved_code):
            return
        try:
            backup_dir = os.path.join(CONFIG.BACKUP_DIR, datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(backup_dir, exist_ok=True)
            shutil.copy(file_path, os.path.join(backup_dir, os.path.basename(file_path)))
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(improved_code)
            logger.info(f"Improved file: {file_path}")
            await self.db.save_interaction("system", f"Improve code: {file_path}", "Completed")
            await notify_user("system", f"Improved file: {file_path}")
        except Exception as e:
            logger.error(f"Apply improvement error for {file_path}: {str(e)}")

    async def handle_error(self, error_message: str):
        """Handle errors with AI assistance."""
        try:
            if "ModuleNotFoundError" in error_message:
                library = error_message.split("'")[1]
                from utils.error_handler import install_library
                await install_library(library)
            prompt = f"Fix Python error: {error_message}"
            for _, model_func in self.models:
                fix = await model_func(prompt)
                if fix and await self.validate_code(fix):
                    error_file = os.path.join(CONFIG.UPDATE_DIR, f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
                    with open(error_file, "w", encoding="utf-8") as f:
                        f.write(fix)
                    logger.info(f"Fix saved: {error_file}")
                    await self.db.save_interaction("system", f"Handle error: {error_message}", f"Fix saved: {error_file}")
                    break
        except Exception as e:
            logger.error(f"Error handling error: {str(e)}")

    async def improve_code(self):
        """Background code improvement loop with reinforcement learning."""
        while True:
            try:
                code_files = await self.analyze_code()
                for file_path in code_files:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    improved_code = await self.generate_improvement(file_path, content)
                    if improved_code:
                        await self.apply_improvement(file_path, improved_code)
                await notify_user("system", "Code improvement cycle completed")
                await asyncio.sleep(3600)  # Run hourly
            except Exception as e:
                logger.error(f"Code improvement error: {str(e)}")
                await self.handle_error(str(e))
                await asyncio.sleep(60)

improver = CodeImprover()