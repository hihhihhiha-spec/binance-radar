import time
import json
import os
import threading
import urllib.request
import pandas as pd
from datetime import datetime
from flask import Flask
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient

app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Futures Radar 24/7 is Active!", 200

@app.route('/health')
def health():
    return "OK", 200

# مخزن بيانات الشموع
candle_data = {}

def get_all_futures_symbols():
    """جلب جميع أزواج USDT النشطة من العقود الآجلة (Futures) بدون حظر IP"""
    try:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            symbols = [
                s['symbol'].lower() for s in data['symbols'] 
                if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING'
            ]
            print(f"✅ تم جلب {len(symbols)} عملة فيوتشرز بنجاح!")
            return symbols
    except Exception as e:
        print(f"⚠️ تعذر جلب القائمة كاملة، سيتم استخدام القائمة الأساسية: {e}")
        return [
            "btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", 
            "adausdt", "dogeusdt", "avaxusdt", "dotusdt", "linkusdt"
        ]

def check_pattern_custom(df):
    """
    فحص الشروط المحددة:
    c1: الشمعة الأولى
    c2: الشمعة الحمراء
    c3: الشمعة الخضراء المليئة داخل نطاق الحمراء
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

        # ب) إغلاق الحمراء يكسر أدنى ذيل (Low) للشمعة المرجعية
        breaks_c1_low = c2['close'] < c1['low']

        if not (is_body_bigger and breaks_c1_low):
            return False

        # -------------------------------------------------------------
        # 2. شروط الشمعة الخضراء (C3)
        # -------------------------------------------------------------
        is_c3_green = c3['close'] > c3['open']
        if not is_c3_green:
            return False

        c3_body = abs(c3['open'] - c3['close'])
        c3_total_range = c3['high'] - c3['low']

        # أ) شمعة مليئة (جسم الشمعة يشكل أكثر من 60% من إجمالي طولها)
        is_full_candle = c3_total_range > 0 and (c3_body / c3_total_range) >= 0.60

        # ب) الشمعة الخضراء متواجدة داخل نطاق الشمعة الحمراء
        is_inside_red = (c3['low'] >= c2['low']) and (c3['high'] <= c2['high'])

        return is_full_candle and is_inside_red

    except Exception:
        return False

def message_handler(_, message):
    """معالجة بث بينانس المباشر للفيوتشرز"""
    try:
        payload = json.loads(message)
        
        kline = None
        if 'k' in payload:
            kline = payload['k']
        elif 'data' in payload and 'k' in payload['data']:
            kline = payload['data']['k']

        if kline:
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

                stored_count = len(candle_data[key])

                if stored_count >= 3:
                    df = pd.DataFrame(candle_data[key])
                    
                    if check_pattern_custom(df):
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print("\n" + "🔥"*30, flush=True)
                        print(f"🚨 [رصد فيوتشرز مؤكد] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}", flush=True)
                        print(f"   📊 إغلاق الخضراء: {kline['c']} | النطاق: داخل الشمعة الحمراء", flush=True)
                        print("🔥"*30 + "\n", flush=True)

    except Exception as e:
        pass

def start_futures_radar():
    """توزيع البث المباشر لجميع عملات العقود الآجلة بدون حظر IP"""
    symbols = get_all_futures_symbols()
    timeframes = ['1m', '3m', '5m', '1h']

    # بناء قوائم البث المباشر
    stream_list = []
    for symbol in symbols:
        for tf in timeframes:
            stream_list.append(f"{symbol}@kline_{tf}")

    print(f"🚀 جاري بدء الاستماع المباشر لـ {len(stream_list)} قناة بث فيوتشرز...", flush=True)

    # استخدام خادم البث المباشر المخصص للفيوتشرز
    futures_ws_url = "wss://fstream.binance.com/ws"
    
    try:
        client = SpotWebsocketStreamClient(
            stream_url=futures_ws_url, 
            on_message=message_handler
        )
        
        # الاشتراك في الدفعات بفاصل بسيط
        batch_size = 200
        for i in range(0, len(stream_list), batch_size):
            batch = stream_list[i:i + batch_size]
            client.subscribe(stream=batch)
            time.sleep(0.1)

        print("✅ تم تفعيل رادار الفيوتشرز لجميع العملات بنجاح!", flush=True)
    except Exception as e:
        print(f"❌ خطأ في الاتصال ببث الفيوتشرز: {e}", flush=True)

if __name__ == "__main__":
    start_futures_radar()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
