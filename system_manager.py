import psutil
import subprocess
import os
import wmi
import winreg
import asyncio
import logging
from config import BASE_DIR
from database import save_interaction
from utils.notify_user import notify_user
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

async def get_system_info(user_id="system"):
    """Отримання інформації про систему."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        gpu = await get_gpu_usage()
        processes = len(list(psutil.process_iter()))
        disk = psutil.disk_usage('/').percent
        network = await get_network_info()
        result = f"Система: CPU {cpu}%, RAM {ram}%, GPU {gpu}, Диск {disk}%, Процесів: {processes}\nМережа: {network}"
        await notify_user(user_id, result)
        await save_interaction(user_id, "system_info", result)
        return result
    except Exception as e:
        logger.error(f"System info error: {str(e)}")
        return f"Помилка: {str(e)}"

async def get_gpu_usage():
    """Отримання використання GPU."""
    try:
        c = wmi.WMI(namespace="root\\CIMV2")
        gpu = c.Win32_PerfFormattedData_PerfProc_Process()[0]
        return f"{gpu.PercentProcessorTime}%"
    except Exception:
        return "Н/Д"

async def get_network_info():
    """Отримання інформації про мережу."""
    try:
        net_io = psutil.net_io_counters()
        return f"Вхід: {net_io.bytes_recv / 1024:.2f} KB, Вихід: {net_io.bytes_sent / 1024:.2f} KB"
    except Exception:
        return "Н/Д"

async def start_program(program_name, user_id="system"):
    """Запуск програми."""
    try:
        if not program_name:
            return "Вкажіть програму!"
        if os.path.exists(program_name):
            subprocess.Popen(program_name)
            result = f"Запущено: {program_name}"
            await notify_user(user_id, result)
            await save_interaction(user_id, f"start_program: {program_name}", result)
            return result
        common_programs = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "browser": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe"
        }
        program_path = common_programs.get(program_name.lower(), program_name)
        for path in os.environ["PATH"].split(os.pathsep):
            full_path = os.path.join(path, program_path)
            if os.path.exists(full_path):
                subprocess.Popen(full_path)
                result = f"Запущено: {program_name}"
                await notify_user(user_id, result)
                await save_interaction(user_id, f"start_program: {program_name}", result)
                return result
        subprocess.Popen(program_path, shell=True)
        result = f"Запущено: {program_name}"
        await notify_user(user_id, result)
        await save_interaction(user_id, f"start_program: {program_name}", result)
        return result
    except Exception as e:
        logger.error(f"Error starting program {program_name}: {str(e)}")
        return f"Помилка запуску: {str(e)}"

async def kill_process(process_name, user_id="system"):
    """Завершення процесу."""
    try:
        if not process_name:
            return "Вкажіть процес!"
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.name().lower() == process_name.lower():
                proc.kill()
                result = f"Процес {process_name} завершено"
                await notify_user(user_id, result)
                await save_interaction(user_id, f"kill_process: {process_name}", result)
                return result
        return f"Процес {process_name} не знайдено"
    except Exception as e:
        logger.error(f"Error killing process {process_name}: {str(e)}")
        return f"Помилка: {str(e)}"

async def get_detailed_process_info():
    """Отримання детальної інформації про процеси."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'exe']):
        try:
            info = proc.as_dict(attrs=['pid', 'name', 'cpu_percent', 'memory_percent', 'exe'])
            threat_analysis = await request_xai_instruction(f"Analyze process {info['name']} for threats")
            processes.append({
                'pid': info['pid'],
                'name': info['name'],
                'cpu_percent': info['cpu_percent'],
                'memory_percent': info['memory_percent'],
                'path': info['exe'] or "Невідомо",
                'threat_analysis': threat_analysis or "Н/Д"
            })
        except:
            continue
    return processes

async def disable_autostart(process_path, user_id="system"):
    """Відключення автозапуску."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE)
        for i in range(1000):
            try:
                name, value, _ = winreg.EnumValue(key, i)
                if process_path.lower() in value.lower():
                    winreg.DeleteValue(key, name)
            except WindowsError:
                break
        winreg.CloseKey(key)
        result = "Автозапуск відключено"
        await notify_user(user_id, result)
        await save_interaction(user_id, f"disable_autostart: {process_path}", result)
        return result
    except Exception as e:
        logger.error(f"Error disabling autostart: {str(e)}")
        return f"Помилка: {str(e)}"

async def is_system_critical(process_name):
    """Перевірка, чи є процес системним."""
    critical_processes = [
        "svchost.exe", "csrss.exe", "wininit.exe", "smss.exe", "lsass.exe",
        "winlogon.exe", "explorer.exe", "dwm.exe", "taskmgr.exe"
    ]
    return process_name.lower() in [p.lower() for p in critical_processes]

async def optimize_resources(user_id="system"):
    """Оптимізація ресурсів."""
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS)
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.pid != os.getpid() and not await is_system_critical(proc.name()):
                proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        result = "Оптимізація завершена"
        await notify_user(user_id, result)
        await save_interaction(user_id, "optimize_resources", result)
        return result
    except Exception as e:
        logger.error(f"Error optimizing resources: {str(e)}")
        return f"Помилка: {str(e)}"