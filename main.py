import sys
import argparse
import logging
import os
import threading
import asyncio
import uvicorn
from fastapi import FastAPI
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from gpt4all import GPT4All
from database import get_context, save_interaction, init_db, get_cached_response
from config import TELEGRAM_TOKEN, MODEL_NAME, BASE_DIR, ENCRYPTION_KEY, XAI_API_KEY
from security import encrypt_data, decrypt_data
from system_manager import get_system_info, start_program, kill_process, optimize_resources
from audio_manager import recognize_telegram_audio, execute_audio_command, speak
from home_control import scan_system, background_monitor, handle_user_confirmation
from crypto_trader import analyze_market, execute_trade, get_open_positions, analyze_user_trades, scalping_strategy, handle_testnet_results, handle_trade_confirmation
from cloud_manager import check_cloud_status, start_cloud_manager
from plugins.github import github_action
from plugins.openai import request_openai
from plugins.file_reader import read_file
from plugins.youtube import play_youtube
from plugins.search import search_query
from plugins.self_learning import learn_response
from plugins.zhanna import init_zhanna_connection, request_zhanna_upgrade
from plugins.self_improvement import improve_code, handle_error
from utils.network import is_online
from utils.notify_user import notify_user
from utils.error_handler import install_library
from server import init_web_server
from gui import start_gui
import winreg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_arguments():
    parser = argparse.ArgumentParser(description="Sakura AI")
    parser.add_argument("--user_id", type=str, help="Telegram User ID for notifications")
    parser.add_argument("--web_only", action="store_true", help="Run only web server")
    parser.add_argument("--bot_only", action="store_true", help="Run only Telegram bot")
    return parser.parse_args()

def setup_autostart():
    """Налаштування автозапуску."""
    try:
        exe_path = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "SakuraAI", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        logger.info("Автозапуск налаштовано.")
    except Exception as e:
        logger.error(f"Помилка налаштування автозапуску: {str(e)}")

async def init_core():
    """Ініціалізація ядра."""
    logger.info("Ініціалізація ядра Сакури...")
    try:
        await init_db()
        await optimize_resources()
        if await is_online():
            await init_zhanna_connection()
        threading.Thread(target=improve_code, daemon=True).start()
        logger.info("Ядро Сакури ініціалізовано.")
    except Exception as e:
        logger.error(f"Помилка ініціалізації ядра: {str(e)}")
        await handle_error(str(e))

async def process_command(command, user_id, model):
    """Обробка команд."""
    try:
        command_lower = command.lower()
        if "організувати торгівлю" in command_lower:
            return await handle_trading_request(command, user_id)
        if "музика" in command_lower or "відтвори" in command_lower:
            return await play_youtube(command, user_id)
        if "пошук" in command_lower or "знайди" in command_lower:
            return await search_query(command.replace("пошук", "").replace("знайди", "").strip(), user_id)
        if "запусти" in command_lower or "відкрий" in command_lower:
            program = command_lower.replace("запусти", "").replace("відкрий", "").strip()
            return await start_program(program, user_id)
        if "заверши" in command_lower or "закрий" in command_lower:
            process = command_lower.replace("заверши", "").replace("закрий", "").strip()
            return await kill_process(process, user_id)
        if "знешкодити" in command_lower:
            return await handle_user_confirmation(command, user_id)
        if "confirm" in command_lower:
            return await handle_trade_confirmation(command, user_id, testnet=True)
        if "github" in command_lower:
            parts = command.split()
            action = parts[1] if len(parts) > 1 else "list"
            repo_name = parts[2] if len(parts) > 2 else None
            return await github_action(action, user_id, repo_name)
        if await is_online():
            from plugins.xai import request_xai
            xai_response = await request_xai(command, mode="deepsearch")
            if xai_response:
                await save_interaction(user_id, command, xai_response)
                await notify_user(user_id, xai_response)
                return xai_response
            zhanna_response = await request_zhanna_upgrade(user_id, command)
            if zhanna_response:
                await save_interaction(user_id, command, zhanna_response)
                await notify_user(user_id, zhanna_response)
                return zhanna_response
            gpt_response = await request_openai(command)
            if gpt_response:
                await save_interaction(user_id, command, gpt_response)
                await notify_user(user_id, gpt_response)
                return gpt_response
        cached_response = await get_cached_response(command)
        if cached_response:
            await notify_user(user_id, cached_response)
            return cached_response
        context_data = await get_context(user_id)
        prompt = f"{context_data}\nUser: {command}"
        response = model.generate(prompt, max_tokens=500)
        await learn_response(command, response)
        await save_interaction(user_id, command, response)
        await notify_user(user_id, response)
        await speak(response, user_id)
        return response
    except Exception as e:
        logger.error(f"Command processing error: {str(e)}")
        await handle_error(str(e))
        return "Помилка обробки команди, працюю над виправленням!"

async def handle_trading_request(command, user_id):
    """Обробка торговельного запиту."""
    try:
        parts = command.split()
        symbol = parts[2].upper() if len(parts) > 2 else "BTC/USDT"
        analysis = await analyze_market(symbol, user_id, testnet=True)
        entry_price = float(analysis.split("Ціна: ")[1].split(" ")[0]) if "Ціна: " in analysis else 0.0
        take_profit = entry_price * 1.07
        stop_loss = entry_price * 0.95
        plan = (
            f"Аналіз ринку Binance: {symbol}\n"
            f"Точка входу: {entry_price:.4f} USDT\n"
            f"Тейк-профіт: {take_profit:.4f} USDT (+7%)\n"
            f"Стоп-лос: {stop_loss:.4f} USDT (-5%)\n"
            f"Команда: /trade buy {symbol} {entry_price}"
        )
        await notify_user(user_id, plan)
        await save_interaction(user_id, f"trade_plan: {symbol}", plan)
        return plan
    except Exception as e:
        logger.error(f"Trading request error: {str(e)}")
        await handle_error(str(e))
        return "Помилка аналізу ринку!"

async def start(update, context):
    user_id = str(update.effective_user.id)
    response = (
        "🔋 Сакура AI активовано!\n"
        "Команди:\n"
        "🎵 /music <назва> - Відтворити музику\n"
        "🔍 /search <запит> - Пошук\n"
        "💻 /run <програма> - Запустити програму\n"
        "🛑 /kill <процес> - Завершити процес\n"
        "📊 /system - Статус системи\n"
        "🔎 /scan - Сканування системи\n"
        "💹 /market - Аналіз ринку\n"
        "📈 /trades - Угоди\n"
        "📉 /trade - Виконати угоду\n"
        "📋 /positions - Позиції\n"
        "🧪 /testnet - Результати Testnet\n"
        "☁️ /cloud - Статус бекапів\n"
        "🚀 /upgrade - Оновлення\n"
        "📁 /read <файл> - Читання файлу\n"
        "📦 /github <дія> - Робота з GitHub"
    )
    await update.message.reply_text(response)
    await save_interaction(user_id, "start", response)
    logger.info(f"User {user_id} started the bot")

async def system_info(update, context):
    user_id = str(update.effective_user.id)
    info = await get_system_info(user_id)
    await update.message.reply_text(f"📊 {info}")
    logger.info(f"User {user_id} requested system info")

async def scan(update, context):
    user_id = str(update.effective_user.id)
    result = await scan_system(user_id)
    await update.message.reply_text(f"🔎 {result}")
    logger.info(f"User {user_id} initiated system scan")

async def market(update, context):
    user_id = str(update.effective_user.id)
    query = " ".join(context.args) if context.args else None
    result = await analyze_market(query, user_id, testnet=True)
    await update.message.reply_text(f"💹 {result}")
    logger.info(f"User {user_id} analyzed market: {query}")

async def trades(update, context):
    user_id = str(update.effective_user.id)
    result = await analyze_user_trades(user_id)
    await update.message.reply_text(f"📈 {result}")
    logger.info(f"User {user_id} analyzed trades")

async def trade(update, context):
    user_id = str(update.effective_user.id)
    command = " ".join(context.args) if context.args else "buy BTC/USDT"
    result = await execute_trade(command, user_id, testnet=True)
    await update.message.reply_text(f"📉 {result}")
    logger.info(f"User {user_id} executed trade: {command}")

async def positions(update, context):
    user_id = str(update.effective_user.id)
    result = await get_open_positions(user_id, testnet=True)
    await update.message.reply_text(f"📋 {result}")
    logger.info(f"User {user_id} checked positions")

async def testnet(update, context):
    user_id = str(update.effective_user.id)
    result = await handle_testnet_results(user_id)
    await update.message.reply_text(f"🧪 {result}")
    logger.info(f"User {user_id} checked testnet results")

async def cloud(update, context):
    user_id = str(update.effective_user.id)
    result = await check_cloud_status(user_id)
    await update.message.reply_text(f"☁️ {result}")
    logger.info(f"User {user_id} checked cloud status")

async def upgrade(update, context):
    user_id = str(update.effective_user.id)
    result = await request_zhanna_upgrade(user_id, "upgrade") if await is_online() else "Немає інтернету"
    await update.message.reply_text(f"🚀 {result}")
    logger.info(f"User {user_id} requested upgrade")

async def music(update, context):
    user_id = str(update.effective_user.id)
    query = " ".join(context.args) if context.args else None
    result = await play_youtube(f"музика {query}", user_id)
    await update.message.reply_text(f"🎵 {result}")
    logger.info(f"User {user_id} requested music: {query}")

async def search(update, context):
    user_id = str(update.effective_user.id)
    query = " ".join(context.args) if context.args else None
    result = await search_query(query, user_id)
    await update.message.reply_text(f"🔍 {result}")
    logger.info(f"User {user_id} searched: {query}")

async def run_program(update, context):
    user_id = str(update.effective_user.id)
    program = " ".join(context.args) if context.args else None
    result = await start_program(program, user_id)
    await update.message.reply_text(f"💻 {result}")
    logger.info(f"User {user_id} ran program: {program}")

async def kill_process_cmd(update, context):
    user_id = str(update.effective_user.id)
    process = " ".join(context.args) if context.args else None
    result = await kill_process(process, user_id)
    await update.message.reply_text(f"🛑 {result}")
    logger.info(f"User {user_id} killed process: {process}")

async def read_file_cmd(update, context):
    user_id = str(update.effective_user.id)
    file_path = " ".join(context.args) if context.args else None
    result = await read_file(file_path, user_id)
    await update.message.reply_text(f"📁 {result}")
    logger.info(f"User {user_id} read file: {file_path}")

async def github_cmd(update, context):
    user_id = str(update.effective_user.id)
    args = context.args
    action = args[0] if args else "list"
    repo_name = args[1] if len(args) > 1 else None
    result = await github_action(action, user_id, repo_name)
    await update.message.reply_text(f"📦 {result}")
    logger.info(f"User {user_id} performed GitHub action: {action}")

async def handle_message(update, context, model):
    user_id = str(update.effective_user.id)
    text = update.message.text
    result = await process_command(text, user_id, model)
    await update.message.reply_text(result)
    logger.info(f"User {user_id} chatted: {text}")

async def handle_voice(update, context, model):
    user_id = str(update.effective_user.id)
    try:
        file = await update.message.voice.get_file()
        audio_path = os.path.join(BASE_DIR, f"voice_{user_id}.ogg")
        await file.download_to_drive(audio_path)
        text = await recognize_telegram_audio(audio_path)
        result = await process_command(text, user_id, model)
        await update.message.reply_text(result)
        await save_interaction(user_id, f"voice: {text}", result)
        os.remove(audio_path)
    except Exception as e:
        logger.error(f"Voice error for user {user_id}: {str(e)}")
        await handle_error(str(e))
        await update.message.reply_text("Помилка обробки голосу!")

async def handle_button(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = query.data
    await query.answer()
    try:
        if data == "system":
            result = await get_system_info(user_id)
        elif data == "scan":
            result = await scan_system(user_id)
        elif data == "market":
            result = await analyze_market(None, user_id, testnet=True)
        elif data == "trades":
            result = await analyze_user_trades(user_id)
        elif data == "trade":
            result = await execute_trade("buy BTC/USDT", user_id, testnet=True)
        elif data == "positions":
            result = await get_open_positions(user_id, testnet=True)
        elif data == "testnet":
            result = await handle_testnet_results(user_id)
        elif data == "cloud":
            result = await check_cloud_status(user_id)
        elif data == "upgrade":
            result = await request_zhanna_upgrade(user_id, "upgrade") if await is_online() else "Немає інтернету"
        elif data == "music":
            result = await play_youtube("музика", user_id)
        elif data == "search":
            result = await search_query("пошук", user_id)
        elif data == "run":
            result = await start_program("notepad", user_id)
        elif data == "kill":
            result = await kill_process("notepad.exe", user_id)
        elif data == "read":
            result = await read_file("sakura.log", user_id)
        elif data == "github":
            result = await github_action("list", user_id)
        else:
            result = "Невідома команда"
        await query.message.reply_text(result)
        await save_interaction(user_id, f"button_{data}", result)
        logger.info(f"User {user_id} pressed button: {data}")
    except Exception as e:
        logger.error(f"Button handling error: {str(e)}")
        await handle_error(str(e))
        await query.message.reply_text("Помилка обробки кнопки!")

async def run_bot(user_id, model):
    logger.info("Starting Telegram bot...")
    try:
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("system", system_info))
        app.add_handler(CommandHandler("scan", scan))
        app.add_handler(CommandHandler("market", market))
        app.add_handler(CommandHandler("trades", trades))
        app.add_handler(CommandHandler("trade", trade))
        app.add_handler(CommandHandler("positions", positions))
        app.add_handler(CommandHandler("testnet", testnet))
        app.add_handler(CommandHandler("cloud", cloud))
        app.add_handler(CommandHandler("upgrade", upgrade))
        app.add_handler(CommandHandler("music", music))
        app.add_handler(CommandHandler("search", search))
        app.add_handler(CommandHandler("run", run_program))
        app.add_handler(CommandHandler("kill", kill_process_cmd))
        app.add_handler(CommandHandler("read", read_file_cmd))
        app.add_handler(CommandHandler("github", github_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: handle_message(update, context, model)))
        app.add_handler(MessageHandler(filters.VOICE, lambda update, context: handle_voice(update, context, model)))
        app.add_handler(CallbackQueryHandler(handle_button))
        threading.Thread(target=lambda: asyncio.run(background_monitor(user_id)), daemon=True).start()
        threading.Thread(target=lambda: asyncio.run(scalping_strategy(user_id, True)), daemon=True).start()
        threading.Thread(target=lambda: asyncio.run(start_cloud_manager(user_id)), daemon=True).start()
        await app.run_polling()
    except Exception as e:
        logger.error(f"Bot error: {str(e)}")
        await handle_error(str(e))

async def main():
    args = setup_arguments()
    user_id = args.user_id or "123456789"
    logger.info("Initializing Sakura AI...")
    try:
        model = GPT4All(MODEL_NAME, model_path=os.path.join(BASE_DIR, "models"), device="cpu", allow_download=False)
        logger.info(f"Model {MODEL_NAME} loaded successfully")
    except Exception as e:
        logger.error(f"Model loading error: {str(e)}")
        await handle_error(str(e))
        sys.exit(1)
    await init_core()
    setup_autostart()
    threading.Thread(target=lambda: asyncio.run(start_gui(model)), daemon=True).start()
    if args.web_only:
        web_app = init_web_server(model)
        await uvicorn.run(web_app, host="0.0.0.0", port=8000)
    elif args.bot_only:
        await run_bot(user_id, model)
    else:
        web_app = init_web_server(model)
        asyncio.create_task(run_bot(user_id, model))
        await uvicorn.run(web_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    asyncio.run(main())