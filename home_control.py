import psutil
import asyncio
import logging
import os
from datetime import datetime
from config import BASE_DIR
from database import save_interaction
from system_manager import get_detailed_process_info, is_system_critical, disable_autostart, kill_process
from utils import notify_user
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

async def scan_system(user_id):
    """Сканування системи на підозрілі процеси."""
    try:
        processes = get_detailed_process_info()
        suspicious = []
        for proc in processes:
            if proc['cpu_percent'] > 80 or proc['memory_percent'] > 50:
                if not is_system_critical(proc['name']):
                    analysis = await request_xai_instruction(f"Analyze process {proc['name']} for potential threats")
                    proc['threat_analysis'] = analysis
                    suspicious.append(proc)
        if suspicious:
            report = "\n".join([f"{p['name']} (PID: {p['pid']}, CPU: {p['cpu_percent']}%, RAM: {p['memory_percent']}%) - {p['threat_analysis']}" for p in suspicious])
            await notify_user(user_id, f"Підозрілі процеси:\n{report}\nЗнешкодити? (/disable <name>)")
            await save_interaction(user_id, "scan_system", report)
            return report
        return "Підозрілих процесів не виявлено"
    except Exception as e:
        logger.error(f"System scan error: {str(e)}")
        return f"Помилка сканування: {str(e)}"

async def get_suspicious_processes():
    """Отримання підозрілих процесів."""
    try:
        processes = get_detailed_process_info()
        return [p for p in processes if p['cpu_percent'] > 80 or p['memory_percent'] > 50]
    except Exception as e:
        logger.error(f"Error getting suspicious processes: {str(e)}")
        return []

async def background_monitor(user_id):
    """Фоновий моніторинг системи."""
    while True:
        try:
            suspicious = await get_suspicious_processes()
            if suspicious:
                report = "\n".join([f"{p['name']} (PID: {p['pid']})" for p in suspicious])
                await notify_user(user_id, f"Виявлено підозрілі процеси:\n{report}")
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Background monitor error: {str(e)}")
            await asyncio.sleep(60)

async def handle_user_confirmation(command, user_id):
    """Обробка підтвердження користувача."""
    try:
        if "disable" in command.lower():
            parts = command.split()
            if len(parts) > 1:
                process_name = parts[1]
                result = disable_autostart(process_name)
                await notify_user(user_id, result)
                return result
        elif "kill" in command.lower():
            parts = command.split()
            if len(parts) > 1:
                process_name = parts[1]
                result = kill_process(process_name, user_id)
                await notify_user(user_id, result)
                return result
        return "Невідома команда підтвердження"
    except Exception as e:
        logger.error(f"Confirmation error: {str(e)}")
        return f"Помилка: {str(e)}"