import asyncio
import json
import os
import threading
import pandas as pd
from datetime import datetime
from flask import Flask
import websockets

# سيرفر وهمي لمنصة Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Binance WebSocket Radar is Running!", 200

@app.route('/health')
def health():
    return "OK", 200

# مخزن لحفظ أحدث الشموع للعملات
candle_data = {}

def check_pattern(df):
    """فحص شروط الشموع"""
    try:
        if df is None or len(df) < 3:
            return False

        prev_candle = df.iloc[-3]
        red_candle = df.iloc[-2]
        green_candle = df.iloc[-1]

        # 1. شمعة حمراء أكبر من التي قبلها وتغلق تحت ذيلها
        is_red = red_candle['close'] < red_candle['open']
        red_body = abs(red_candle['close'] - red_candle['open'])
        prev_body = abs(prev_candle['close'] - prev_candle['open'])
        
        is_bigger = red_body > prev_body
        breaks_lower_tail = red_candle['close'] < prev_candle['low']

        if not (is_red and is_bigger and breaks_lower_tail):
            return False

        # 2. شمعة خضراء تالية تغلق عند نصف الشمعة الحمراء على الأقل
        is_green = green_candle['close'] > green_candle['open']
        red_midpoint = red_candle['open'] - (red_body / 2)
        closes_at_half = green_candle['close'] >= red_midpoint

        return is_green and closes_at_half
    except Exception:
        return False

async def process_kline(data):
    """معالجة بيانات الشموع القادمة عبر البث المباشر WebSocket"""
    try:
        kline = data['k']
        symbol = kline['s']
        tf = kline['i']
        is_closed = kline['x']  # إغلاق الشمعة

        # نحدث البيانات فقط عند إغلاق الشمعة
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

            # الاحتفاظ بآخر 5 شموع فقط
            if len(candle_data[key]) > 5:
                candle_data[key].pop(0)

            if len(candle_data[key]) >= 3:
                df = pd.DataFrame(candle_data[key])
                if check_pattern(df):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print("\n" + "="*60)
                    print(f"🚨 [رصد المباشر WEBSOCKET] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}")
                    print("="*60 + "\n")
    except Exception as e:
        print(f"⚠️ خطأ معالجة الشمعة: {e}")

async def start_websocket():
    """الاتصال المباشر ببث بينانس (WebSocket Multi-Stream)"""
    # أهم العملات الأساسية مقابل USDT (يمكنك إضافة أو تغيير العملات)
    top_symbols = [
        "btc usdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "adausdt", 
        "dogeusdt", "avaxusdt", "dotusdt", "linkusdt", "nearusdt", "ltcusdt"
    ]
    timeframes = ['1m', '3m', '5m', '1h']

    # تجهيز روابط البث المباشر
    streams = []
    for s in top_symbols:
        symbol_clean = s.replace(" ", "").lower()
        for tf in timeframes:
            streams.append(f"{symbol_clean}@kline_{tf}")

    stream_url = f"wss://stream.binance.com:9443/ws/" + "/".join(streams)

    print("🚀 جاري الاتصال بـ Binance WebSockets (بث مباشر بدبي حظر IP)...")

    while True:
        try:
            async with websockets.connect(stream_url) as ws:
                print("✅ تم الاتصال بالبث المباشر بنجاح! السكربت يستمع للشموع الآن...")
                while True:
                    response = await ws.recv()
                    data = json.loads(response)
                    if 'k' in data:
                        await process_kline(data)
        except Exception as e:
            print(f"🌐 [انقطاع مؤقت للبث]: {e} | إعادة الاتصال خلال 5 ثوانٍ...")
            await asyncio.sleep(5)

def run_async_radar():
    """تشغيل الحلقة التزامنية للـ Asyncio"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket())

if __name__ == "__main__":
    # تشغيل WebSocket في الخلفية
    threading.Thread(target=run_async_radar, daemon=True).start()

    # تشغيل سيرفر Flask المخصص لمنصة Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
