import time
import json
import os
import threading
import pandas as pd
from datetime import datetime
from flask import Flask
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient

# 1. إنشاء سيرفر Flask لمنصة Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Radar (WebSocket) is Active 24/7!", 200

@app.route('/health')
def health():
    return "OK", 200

# مخزن لحفظ البيانات المؤقتة
candle_data = {}

def check_pattern(df):
    """فحص شرط الشموع المطلوبة"""
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

def message_handler(_, message):
    """معالجة الرسائل القادمة من البث المباشر"""
    try:
        payload = json.loads(message)
        
        # استخراج الشمعة
        kline = None
        if 'k' in payload:
            kline = payload['k']
        elif 'data' in payload and 'k' in payload['data']:
            kline = payload['data']['k']

        if kline:
            symbol = kline['s']
            tf = kline['i']
            is_closed = kline['x']  # الفحص عند الإغلاق فقط

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

                stored_count = len(candle_data[key])
                print(f"📥 [إغلاق شمعة] | {symbol} | فريم: {tf} | السعر: {kline['c']} | مخزن: {stored_count}/3", flush=True)

                if stored_count >= 3:
                    df = pd.DataFrame(candle_data[key])
                    if check_pattern(df):
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print("\n" + "="*60, flush=True)
                        print(f"🚨 [تم الرصد بنجاح] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}", flush=True)
                        print("="*60 + "\n", flush=True)
    except Exception as e:
        pass

def start_radar():
    """تشغيل البث المباشر"""
    symbols = [
        "btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", 
        "adausdt", "dogeusdt", "avaxusdt", "dotusdt", "linkusdt"
    ]
    timeframes = ['1m', '3m', '5m', '1h']

    stream_list = [f"{s}@kline_{tf}" for s in symbols for tf in timeframes]

    print("🚀 جاري الاتصال ببث بينانس المباشر...", flush=True)
    try:
        client = SpotWebsocketStreamClient(on_message=message_handler)
        client.subscribe(stream=stream_list)
        print("✅ تم الاشتراط في العملات بنجاح! الرادار يفحص الشموع الآن...", flush=True)
    except Exception as e:
        print(f"❌ خطأ في البث: {e}", flush=True)

if __name__ == "__main__":
    # 1. البدء بفتح اتصال الرادار أولاً
    start_radar()

    # 2. تشغيل سيرفر Flask بعد ذلك
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
