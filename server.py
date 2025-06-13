from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import asyncio
from config import BASE_DIR, DB_PATH
from system_manager import get_system_info, start_program, kill_process
from home_control import scan_system
from crypto_trader import analyze_market, execute_trade, get_open_positions, analyze_user_trades, handle_testnet_results
from cloud_manager import check_cloud_status
from plugins.file_reader import read_file
from plugins.youtube import play_youtube
from plugins.search import search_query
from plugins.zhanna import request_zhanna_upgrade
from database import save_interaction, get_context
from audio_manager import recognize_speech, speak
from plugins.self_learning import learn_response
from utils.network import is_online
from main import process_command
from tts import router as tts_router

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.include_router(tts_router, prefix="/tts")

def init_web_server(model):
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT user_id, query, response, timestamp FROM history ORDER BY timestamp DESC LIMIT 10")
            history = c.fetchall()
            c.execute("SELECT process_name, cpu_percent, memory_percent, path, status, timestamp FROM suspicious_processes ORDER BY timestamp DESC LIMIT 10")
            suspicious = c.fetchall()
            c.execute("SELECT user_id, symbol, side, quantity, price, status, is_testnet, timestamp FROM trades ORDER BY timestamp DESC LIMIT 10")
            trades = c.fetchall()
            c.execute("SELECT user_id, upgrade_request, status, timestamp FROM upgrades ORDER BY timestamp DESC LIMIT 10")
            upgrades = c.fetchall()
            conn.close()
            online_status = await is_online()
            market_data = await analyze_market(None, "web_user", testnet=True)
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "history": history,
                "suspicious": suspicious,
                "trades": trades,
                "upgrades": upgrades,
                "online_status": online_status,
                "market_data": market_data[:1000]  # Обмеження для відображення
            })
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            return HTMLResponse(f"Помилка: {str(e)}", status_code=500)

    @app.get("/api/market-data")
    async def market_data(symbol: str = "ALL"):
        try:
            data = await analyze_market(symbol if symbol != "ALL" else None, "web_user", testnet=True)
            # Форматування для Chart.js
            return {
                "labels": [f"Time {i}" for i in range(10)],  # Placeholder
                "symbols": [{"name": symbol or "ALL", "prices": [float(d.split("Ціна: ")[1].split(" ")[0]) for d in data.split("\n") if "Ціна: " in d][:10]}]
            }
        except Exception as e:
            logger.error(f"Market data API error: {str(e)}")
            return {"error": str(e)}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        user_id = "web_user"
        while True:
            try:
                data = await websocket.receive_json()
                command = data.get("command")
                if command == "voice":
                    text = await recognize_speech()
                    response = await process_command(text, user_id, model)
                elif command == "upgrade":
                    response = await request_zhanna_upgrade(user_id, command) if await is_online() else "Немає інтернету"
                elif command:
                    response = await process_command(command, user_id, model)
                else:
                    response = "Невідома команда"
                await learn_response(command, response)
                await websocket.send_json({"response": response, "type": "text"})
                await speak(response, user_id)
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                from plugins.self_improvement import handle_error
                await handle_error(str(e))
                await websocket.send_json({"error": str(e)})
                break

    return app