import time
import json
import os
import threading
import requests
import websocket
import pandas as pd
from datetime import datetime
from flask import Flask

# 1. إنشاء تطبيق Flask لبيئة Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Futures Full Radar is Active 24/7!", 200

@app.route('/health')
def health():
    return "OK", 200

# مخزن لحفظ الشموع الأخيرة
candle_data = {}

def get_all_futures_symbols():
    """جلب جميع أزواج USDT النشطة من العقود الآجلة (Futures) مع التمويه لتفادي حظر Binance"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    # محاولة الجلب من رابط Binance الرئيسي
    urls = [
        "https://fapi.binance.com/fapi/v1/exchangeInfo",
        "https://fapi.binance.info/fapi/v1/exchangeInfo"  # رابط احتياطي رسمي من بينانس
    ]

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                symbols = [
                    s['symbol'].lower() for s in data['symbols'] 
                    if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING'
                ]
                if symbols:
                    print(f"✅ تم جلب جميع عملات الفيوتشرز: {len(symbols)} عملة بنجاح!", flush=True)
                    return symbols
        except Exception as e:
            print(f"⚠️ فشلت المحاولة عبر {url}: {e}", flush=True)
            continue

    print("⚠️ تعذر جلب القائمة كاملة، استخدام قائمة الطوارئ الموسعة...", flush=True)
    return [
        "btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "adausdt", "dogeusdt", 
        "avaxusdt", "linkusdt", "nearusdt", "maticusdt", "dotusdt", "ltcusdt", "trxusdt"
    ]

def check_pattern_strict(df):
    """
    فحص الشروط المحددة بدقة:
    c1: الشمعة الأولى المرجعية
    c2: الشمعة الحمراء (تكسر ذيل c1 وجسمها أكبر من c1)
    c3: الشمعة الخضراء (بالكامل شاملاً الأذيال والجسم داخل نطاق c2)
    """
    try:
        if df is None or len(df) < 3:
            return False

        c1 = df.iloc[-3]
        c2 = df.iloc[-2]
        c3 = df.iloc[-1]

        # 1. شروط الشمعة الحمراء (C2)
        is_c2_red = c2['close'] < c2['open']
        if not is_c2_red:
            return False

        c2_body = abs(c2['open'] - c2['close'])
        c1_body = abs(c1['open'] - c1['close'])

        is_body_bigger = c2_body > c1_body
        breaks_c1_low = c2['close'] < c1['low']

        if not (is_body_bigger and breaks_c1_low):
            return False

        # 2. شروط الشمعة الخضراء (C3)
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

    if is_closed:
        key = f"{symbol}_{tf}"
        if key not in candle_data:
            candle_data[key] = []

        candle_data[key].append({
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c'])
        })

        if len(candle_data[key]) > 5:
            candle_data[key].pop(0)

        if len(candle_data[key]) >= 3:
            df = pd.DataFrame(candle_data[key])
            
            if check_pattern_strict(df):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("\n" + "🔥"*30, flush=True)
                print(f"🚨 [رصد فيوتشرز مؤكد] | العملة: {symbol.upper()} | الفريم: {tf} | الوقت: {now}", flush=True)
                print(f"   📊 إغلاق الخضراء: {kline['c']} | محتواة بالكامل داخل الحمراء [Low: {df.iloc[-2]['low']}, High: {df.iloc[-2]['high']}]", flush=True)
                print("🔥"*30 + "\n", flush=True)
            else:
                print(f"🔍 [فحص مغلق]: {symbol.upper()} ({tf}) - غير متطابق", flush=True)

def on_message(ws, message):
    try:
        payload = json.loads(message)
        if 'data' in payload and 'k' in payload['data']:
            process_kline(payload['data']['k'])
        elif 'k' in payload:
            process_kline(payload['k'])
    except Exception:
        pass

def on_error(ws, error):
    pass

def on_close(ws, close_status_code, close_msg):
    time.sleep(5)

def run_ws_chunk(streams_chunk):
    streams_url = "/".join(streams_chunk)
    url = f"wss://fstream.binance.com/stream?streams={streams_url}"
    
    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever(ping_interval=60, ping_timeout=10)

def start_futures_radar():
    symbols = get_all_futures_symbols()
    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h']

    all_streams = [f"{symbol}@kline_{tf}" for symbol in symbols for tf in timeframes]

    print(f"🚀 جاري بدء الاستماع المباشر لـ {len(all_streams)} قناة بث للفيوتشرز...", flush=True)

    chunk_size = 400
    for i in range(0, len(all_streams), chunk_size):
        chunk = all_streams[i:i + chunk_size]
        t = threading.Thread(target=run_ws_chunk, args=(chunk,))
        t.daemon = True
        t.start()
        time.sleep(1)

    print("✅ تم توزيع البث المباشر لجميع عملات الفيوتشرز بنجاح!", flush=True)

# تشغيل البث في Thread منفصل
threading.Thread(target=start_futures_radar, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
