import time
import json
import os
import threading
import urllib.request
import websocket
import pandas as pd
from datetime import datetime
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Futures Full Radar is Live 24/7!", 200

@app.route('/health')
def health():
    return "OK", 200

# مخزن بيانات الشموع
candle_data = {}

def get_all_futures_symbols():
    """جلب جميع أزواج USDT النشطة من الفيوتشرز بنسبة 100%"""
    try:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            symbols = [
                s['symbol'].lower() for s in data['symbols'] 
                if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING'
            ]
            print(f"✅ تم جلب جميع عملات الفيوتشرز: {len(symbols)} عملة بنجاح!", flush=True)
            return symbols
    except Exception as e:
        print(f"⚠️ خطأ في جلب القائمة، جاري استخدام القائمة الطارئة: {e}", flush=True)
        return ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "adausdt", "dogeusdt", "avaxusdt"]

def check_pattern_strict(df):
    """
    فحص الشرط بدقة متناهية:
    c1: الأولى المرجعية
    c2: الحمراء (تكسر ذيل الأولى، جسمها أكبر)
    c3: الخضراء (بأكملها شاملة الأذيال داخل نطاق الشمعة الحمراء)
    """
    try:
        if df is None or len(df) < 3:
            return False

        c1 = df.iloc[-3]
        c2 = df.iloc[-2]
        c3 = df.iloc[-1]

        # -------------------------------------------------------------
        # 1. شروط الشمعة الحمراء (C2)
        # -------------------------------------------------------------
        is_c2_red = c2['close'] < c2['open']
        if not is_c2_red:
            return False

        c2_body = abs(c2['open'] - c2['close'])
        c1_body = abs(c1['open'] - c1['close'])

        # أ) جسم الحمراء أكبر من جسم الشمعة المرجعية
        is_body_bigger = c2_body > c1_body

        # ب) إغلاق الحمراء يكسر أدنى سعر (Low) للشمعة المرجعية
        breaks_c1_low = c2['close'] < c1['low']

        if not (is_body_bigger and breaks_c1_low):
            return False

        # -------------------------------------------------------------
        # 2. شروط الشمعة الخضراء (C3)
        # -------------------------------------------------------------
        is_c3_green = c3['close'] > c3['open']
        if not is_c3_green:
            return False

        # أ) الشمعة الخضراء بالكامل (بأذيالها وجسمها) تتواجد داخل نطاق الشمعة الحمراء بالكامل
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
                print(f"🚨 [رصد فيوتشرز مؤكد] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}", flush=True)
                print(f"   📊 إغلاق الخضراء: {kline['c']} | داخل نطاق الحمراء بالكامل [Low: {df.iloc[-2]['low']}, High: {df.iloc[-2]['high']}]", flush=True)
                print("🔥"*30 + "\n", flush=True)

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
    """فتح اتصال WebSocket لكل مجموعة قنوات دون تجاوز حدود بينانس"""
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

    # تقسيم القنوات إلى مجموعات (500 قناة لكل اتصال) لتجنب حد بينانس (1024)
    chunk_size = 500
    for i in range(0, len(all_streams), chunk_size):
        chunk = all_streams[i:i + chunk_size]
        t = threading.Thread(target=run_ws_chunk, args=(chunk,))
        t.daemon = True
        t.start()
        time.sleep(1)

    print("✅ تم توزيع واستقبال البث الحي لجميع عملات الفيوتشرز بنجاح!", flush=True)

if __name__ == "__main__":
    start_futures_radar()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
