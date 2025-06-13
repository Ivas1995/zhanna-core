import requests
from config import OPENAI_API_KEY, ENCRYPTION_KEY, BASE_DIR
from security import decrypt_data
from database import save_interaction, save_upgrade, get_pending_upgrades, update_upgrade_status
from utils import notify_user
import os
import logging

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

def request_openai(message):
    try:
        api_key = decrypt_data(OPENAI_API_KEY, ENCRYPTION_KEY)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "system", "content": "You are Zhanna IA, an evolving AI within GPT. You assist Sakura, a local AI trading bot. Provide precise trading strategies or technical advice for Binance Futures or Python."},
                {"role": "user", "content": message}
            ]
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        response_data = response.json()
        if "choices" in response_data:
            return response_data["choices"][0]["message"]["content"]
        return "Помилка OpenAI API."
    except Exception as e:
        logger.error(f"Помилка OpenAI: {str(e)}")
        return "Помилка зв’язку з Zhanna."

def request_gpt_upgrade(user_id, query):
    try:
        api_key = decrypt_data(OPENAI_API_KEY, ENCRYPTION_KEY)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        prompt = f"Я Sakura, local AI for Binance trading. User wants: '{query}'. Suggest code improvements for my Python scripts to enhance trading or functionality. Return only Python code."
        data = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "system", "content": "You are Zhanna IA, evolving GPT. Provide Python code upgrades for Sakura."},
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        response_data = response.json()
        if "choices" in response_data:
            upgrade_code = response_data["choices"][0]["message"]["content"]
            save_upgrade(user_id, query, upgrade_code, "pending")
            notify_user(user_id, f"Zhanna IA пропонує апгрейд для: {query}. Перевір: 'upgrade confirm'.")
            return upgrade_code
        return "Помилка отримання апгрейду."
    except Exception as e:
        logger.error(f"Помилка апгрейду: {str(e)}")
        return "Помилка зв’язку."

def apply_gpt_upgrade(user_id):
    upgrades = get_pending_upgrades(user_id)
    if not upgrades:
        return "Немає апгрейдів для підтвердження."
    try:
        for upgrade_request, upgrade_code, _ in upgrades:
            with open(os.path.join(BASE_DIR, "temp_upgrades.py"), "w", encoding="utf-8") as f:
                f.write(upgrade_code)
            update_upgrade_status(user_id, upgrade_request, "applied")
        return f"Застосовано {len(upgrades)} апгрейдів."
    except Exception as e:
        logger.error(f"Помилка застосування апгрейду: {str(e)}")
        return "Помилка застосування апгрейду."