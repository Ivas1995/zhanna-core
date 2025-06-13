import ccxt.async_support as ccxt
import pandas as pd
import ta
import asyncio
import logging
import os
from datetime import datetime
from config import BASE_DIR, BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_API_SECRET, ENCRYPTION_KEY
from database import save_trade, get_trades, save_cached_response, get_cached_response
from security import decrypt_data
from utils import notify_user
from plugins.search import search_query
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

async def get_binance_symbols(exchange):
    try:
        markets = await exchange.load_markets()
        return [symbol for symbol in markets if symbol.endswith('/USDT') and markets[symbol]['quoteVolume'] > 1000000]
    except Exception as e:
        logger.error(f"Error fetching Binance symbols: {str(e)}")
        return []

async def analyze_market(symbol, user_id, testnet=True, leverage=1):
    cached_key = f"market_{symbol or 'all'}_{testnet}"
    cached = await get_cached_response(cached_key)
    if cached:
        await notify_user(user_id, f"Кешовано: {cached}")
        return cached
    try:
        exchange = ccxt.binance({
            'apiKey': decrypt_data(BINANCE_TESTNET_API_KEY, ENCRYPTION_KEY),
            'secret': decrypt_data(BINANCE_TESTNET_API_SECRET, ENCRYPTION_KEY),
            'enableRateLimit': True,
            'urls': {'api': 'https://testnet.binance.vision/api'} if testnet else {}
        })
        if leverage > 1:
            await exchange.set_leverage(leverage, symbol)
        if not symbol:
            symbols = await get_binance_symbols(exchange)
            analysis = []
            for sym in symbols[:20]:
                result = await analyze_single_symbol(exchange, sym, user_id)
                analysis.append(result)
            await exchange.close()
            result_text = "\n\n".join(analysis)
            news = await search_query("crypto market news", user_id)
            result_text += f"\n\nРинкові новини: {news}"
            await save_cached_response(cached_key, result_text)
            await notify_user(user_id, result_text)
            return result_text
        else:
            result = await analyze_single_symbol(exchange, symbol, user_id)
            await exchange.close()
            await save_cached_response(cached_key, result)
            await notify_user(user_id, result)
            return result
    except Exception as e:
        logger.error(f"Market analysis error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка аналізу ринку: {str(e)}"

async def analyze_single_symbol(exchange, symbol, user_id):
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        df['ma20'] = ta.trend.SMAIndicator(df['close'], window=20).sma()
        df['bollinger'] = ta.volatility.BollingerBands(df['close']).bollinger_mavg()  # Mean Reversion
        latest = df.iloc[-1]
        entry_price = latest['close']
        take_profit = entry_price * 1.07
        stop_loss = entry_price * 0.95
        strategy = "Лонг" if latest['close'] > latest['ma20'] else "Шорт"
        if latest['close'] < latest['bollinger'] * 0.98:
            strategy = "Mean Reversion Buy"
        news = await search_query(f"{symbol.replace('/USDT', '')} crypto news", user_id)
        top_strategies = await request_xai_instruction(f"Top Binance futures scalping strategies for {symbol}")
        analysis = (
            f"Аналіз {symbol}:\n"
            f"Ціна: {entry_price:.4f} USDT\n"
            f"RSI: {latest['rsi']:.2f}\n"
            f"MA20: {latest['ma20']:.4f}\n"
            f"Bollinger: {latest['bollinger']:.4f}\n"
            f"Тейк-профіт: {take_profit:.4f} (+7%)\n"
            f"Стоп-лос: {stop_loss:.4f} (-5%)\n"
            f"Рекомендація: {strategy}\n"
            f"Новини: {news}\n"
            f"Стратегії топ-трейдерів: {top_strategies}"
        )
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {str(e)}")
        return f"Помилка аналізу {symbol}: {str(e)}"

async def execute_trade(command, user_id, testnet=True, leverage=1):
    try:
        parts = command.split()
        side = parts[0].lower()
        symbol = parts[1].upper()
        quantity = float(parts[2]) if len(parts) > 2 else 1.0
        exchange = ccxt.binance({
            'apiKey': decrypt_data(BINANCE_TESTNET_API_KEY, ENCRYPTION_KEY),
            'secret': decrypt_data(BINANCE_TESTNET_API_SECRET, ENCRYPTION_KEY),
            'enableRateLimit': True,
            'urls': {'api': 'https://testnet.binance.vision/api'} if testnet else {}
        })
        if leverage > 1:
            await exchange.set_leverage(leverage, symbol)
        ticker = await exchange.fetch_ticker(symbol)
        price = ticker['last']
        order = await exchange.create_market_order(symbol, side, quantity)
        await save_trade(user_id, symbol, side, quantity, price, "completed", testnet)
        await notify_user(user_id, f"Угоду виконано: {side} {quantity} {symbol} @ {price}")
        await exchange.close()
        return f"Угоду виконано: {side} {quantity} {symbol} @ {price}"
    except Exception as e:
        logger.error(f"Trade execution error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка виконання угоди: {str(e)}"

async def get_open_positions(user_id, testnet=True):
    try:
        exchange = ccxt.binance({
            'apiKey': decrypt_data(BINANCE_TESTNET_API_KEY, ENCRYPTION_KEY),
            'secret': decrypt_data(BINANCE_TESTNET_API_SECRET, ENCRYPTION_KEY),
            'enableRateLimit': True,
            'urls': {'api': 'https://testnet.binance.vision/api'} if testnet else {}
        })
        balance = await exchange.fetch_balance()
        positions = []
        for asset, info in balance.get('info', {}).get('assets', {}).items():
            if float(info.get('free', 0)) > 0:
                positions.append(f"{asset}: {info['free']}")
        await exchange.close()
        return "\n".join(positions) or "Немає відкритих позицій"
    except Exception as e:
        logger.error(f"Positions error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка отримання позицій: {str(e)}"

async def analyze_user_trades(user_id, testnet=True):
    try:
        trades = await get_trades(user_id, testnet)
        if not trades:
            return "Немає угод"
        analysis = "\n".join([f"{t[0]} {t[1]}: {t[2]} @ {t[3]} ({t[4]})" for t in trades])
        return analysis
    except Exception as e:
        logger.error(f"Trade analysis error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка аналізу угод: {str(e)}"

async def handle_testnet_results(user_id):
    try:
        trades = await get_trades(user_id, testnet=True)
        if not trades:
            return "Немає угод у Testnet"
        total_profit = sum([t[3] * (1 if t[1] == "buy" else -1) for t in trades])
        return f"Testnet результати: Загальний профіт {total_profit:.2f} USDT"
    except Exception as e:
        logger.error(f"Testnet results error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка результатів Testnet: {str(e)}"

async def handle_trade_confirmation(command, user_id, testnet=True):
    try:
        return await execute_trade(command.replace("confirm", "").strip(), user_id, testnet)
    except Exception as e:
        logger.error(f"Trade confirmation error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка підтвердження угоди: {str(e)}"

async def scalping_strategy(user_id, testnet=True):
    while True:
        try:
            await analyze_market(None, user_id, testnet=True)
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Scalping strategy error: {str(e)}")
            from plugins.self_improvement import handle_error
            await handle_error(str(e))
            await asyncio.sleep(60)