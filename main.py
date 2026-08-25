import asyncio
import json
import os
import threading
import aiohttp
import pandas as pd
from datetime import datetime
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Radar Active 24/7", 200

@app.route('/health')
def health():
    return "OK", 200

candle_data = {}

def get_all_futures_symbols():
    try:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        import requests
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            symbols = [
                s['symbol'].lower() for s in data['symbols'] 
                if s['quoteAsset'] == 'USDT' and s['contractType'] == 'PERPETUAL' and s['status'] == 'TRADING'
            ]
            if len(symbols) > 50:
                print(f"✅ تم جلب جميع عملات الفيوتشرز: {len(symbols)} عملة!", flush=True)
                return symbols
    except Exception as e:
        print(f"⚠️ خطأ جلب العملات: {e}", flush=True)

    return ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "adausdt", "dogeusdt"]

def check_pattern_strict(df):
    try:
        if df is None or len(df) < 3:
            return False

        c1 = df.iloc[-3]
        c2 = df.iloc[-2]
        c3 = df.iloc[-1]

        # 1. الشمعة الحمراء C2
        is_c2_red = c2['close'] < c2['open']
        if not is_c2_red:
            return False

        c2_body = abs(c2['open'] - c2['close'])
        c1_body = abs(c1['open'] - c1['close'])

        is_body_bigger = c2_body > c1_body
        breaks_c1_low = c2['close'] < c1['low']

        if not (is_body_bigger and breaks_c1_low):
            return False

        # 2. الشمعة الخضراء C3
        is_c3_green = c3['close'] > c3['open']
        if not is_c3_green:
            return False

        is_fully_inside_red = (c3['low'] >= c2['low']) and (c3['high'] <= c2['high'])
        return is_fully_inside_red

    except Exception:
        return False

def process_kline(kline):
    symbol = kline['s']
    tf = kline['i']
    is_closed = kline['x']

    key = f"{symbol}_{tf}"
    if key not in candle_data:
        candle_data[key] = []

    if is_closed:
        candle_data[key].append({
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c'])
        })

        if len(candle_data[key]) > 5:
            candle_data[key].pop(0)

        if len(candle_data[key]) < 3:
            print(f"⏳ [تجميع]: {symbol.upper()} ({tf}) - شمعة {len(candle_data[key])}/3", flush=True)
        else:
            df = pd.DataFrame(candle_data[key])
            if check_pattern_strict(df):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("\n" + "🔥"*30, flush=True)
                print(f"🚨 [فرصة مؤكدة] | العملة: {symbol.upper()} | الفريم: {tf} | الوقت: {now}", flush=True)
                print(f"   📊 إغلاق: {kline['c']} | داخل نطاق الحمراء [Low: {df.iloc[-2]['low']}, High: {df.iloc[-2]['high']}]", flush=True)
                print("🔥"*30 + "\n", flush=True)
            else:
                print(f"🔍 [فحص]: {symbol.upper()} ({tf}) - غير متطابق", flush=True)

async def listen_ws_chunk(session, streams_chunk):
    streams_url = "/".join(streams_chunk)
    url = f"wss://fstream.binance.com/stream?streams={streams_url}"
    
    while True:
        try:
            async with session.ws_connect(url, heartbeat=20) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        payload = json.loads(msg.data)
                        if 'data' in payload and 'k' in payload['data']:
                            process_kline(payload['data']['k'])
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
        except Exception:
            await asyncio.sleep(5)

async def start_async_radar():
    symbols = get_all_futures_symbols()
    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h']
    all_streams = [f"{symbol}@kline_{tf}" for symbol in symbols for tf in timeframes]

    print(f"🚀 جاري ربط {len(all_streams)} قناة بث عبر aiohttp Async...", flush=True)

    chunk_size = 100
    chunks = [all_streams[i:i + chunk_size] for i in range(0, len(all_streams), chunk_size)]

    async with aiohttp.ClientSession() as session:
        tasks = [listen_ws_chunk(session, chunk) for chunk in chunks]
        print("✅ تم تفعيل الاستماع اللحظي المستقر بنجاح!", flush=True)
        await asyncio.gather(*tasks)

def run_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_async_radar())

threading.Thread(target=run_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
