import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest
from config import TELEGRAM_TOKEN, BASE_DIR
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

async def setup_bot():
    try:
        bot = Bot(token=TELEGRAM_TOKEN, request=HTTPXRequest())
        commands = [
            {"command": "start", "description": "Почати роботу"},
            {"command": "music", "description": "Відтворити музика"},
            {"command": "search", "description": "Пошук в інтернеті"},
            {"command": "run", "run": "Запустити програму"},
            {"command": "kill", "kill": "Завершено процес"},
            {"command": "system", "description": "Інформація про систему"},
            {"command": "scan", "description": "Сканувати систему"},
            {"command": "market", "description": "Аналіз крипторинку"},
            {"command": "trades", "description": "Аналіз угод"},
            {"command": "trade", "description": "Виконав угоду"},
            {"command": "positions", "description": "Відкриті позиції"},
        {"command": "testnet", "description": "Результати Testnet"},
            {"command": "cloud", "description": "Статус резервного копіювання"},
            {"command": "upgrade", "description": "Запит на апгрейд"}
        ]
        await bot.set_my_commands(commands)
        keyboard = [
            [
                InlineKeyboardButton("🔋 Система", callback_data="system"),
                InlineKeyboardButton("🔍 Скан", callback_data="scan")
            ],
            [
                InlineKeyboardButton("🎵 Крипторинок", callback_data="market"),
                InlineKeyboardButton("📈 Угоди", callback_data="trades")
            ],
            [
                InlineKeyboardButton("📉 Позиції", callback_data="positions"),
                InlineKeyboardButton("🧪 Testnet", callback_data="testnet")
            ],
            [
                InlineKeyboardButton("☁️ Резерв", callback_data="cloud"),
                InlineKeyboardButton("🚀 Апгрейд", callback_data="upgrade")
            ],
            [
                InlineKeyboardButton("🎵 Музыка", callback_data="music"),
                InlineKeyboardButton("🔍 Пошук", callback_data="search")
            ],
            [
                InlineKeyboardButton("💻 Запуск", callback_data="run"),
                InlineKeyboardButton("🛑 Стоп", callback_data="kill")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(chat_id=123456789, text="🔴 JARVIS: Оберіть команду:", reply_markup=reply_markup))
        logger.info("Telegram bot configured successfully")
        print("Bot configured successfully!")
    except Exception as e:
        logger.error(f"Error configuring bot: {str(e)}")
        from plugins.self_improvement import handle_error
        asyncio.run(handle_error(str(e)))
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(setup_bot())