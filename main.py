import time
import json
import os
import threading
import pandas as pd
from datetime import datetime
from flask import Flask
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient

app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Precise Radar is Live 24/7!", 200

@app.route('/health')
def health():
    return "OK", 200

# مخزن البيانات
candle_data = {}

def check_pattern_precise(df):
    """
    فحص دقيق جداً لشروط الشموع الثلاث:
    df.iloc[-3] : الشمعة الأولى (المرجعية)
    df.iloc[-2] : الشمعة الثانية (الحمراء)
    df.iloc[-1] : الشمعة الثالثة (الخضراء الانعكاسية)
    """
    try:
        if df is None or len(df) < 3:
            return False

        c1 = df.iloc[-3] # الشمعة الأولى
        c2 = df.iloc[-2] # الشمعة الحمراء
        c3 = df.iloc[-1] # الشمعة الخضراء

        # -------------------------------------------------------------
        # 1. شروط الشمعة الثانية (الحمراء)
        # -------------------------------------------------------------
        is_c2_red = c2['close'] < c2['open']
        if not is_c2_red:
            return False

        c2_body = abs(c2['open'] - c2['close'])
        c1_body = abs(c1['open'] - c1['close'])

        # أ) جسم الحمراء أكبر من جسم الشمعة التي قبلها
        is_body_bigger = c2_body > c1_body

        # ب) إغلاق الحمراء يكسر أدنى ذيل (Low) للشمعة الأولى
        breaks_c1_low = c2['close'] < c1['low']

        if not (is_body_bigger and breaks_c1_low):
            return False

        # -------------------------------------------------------------
        # 2. شروط الشمعة الثالثة (الخضراء الانعكاسية)
        # -------------------------------------------------------------
        is_c3_green = c3['close'] > c3['open']
        if not is_c3_green:
            return False

        # حساب النقطة الوسطى لجسم الشمعة الحمراء بدقة
        red_body_midpoint = (c2['open'] + c2['close']) / 2.0

        # ج) إغلاق الخضراء يكون أعلى أو يساوي منتصف جسم الشمعة الحمراء
        closes_above_midpoint = c3['close'] >= red_body_midpoint

        return closes_above_midpoint

    except Exception:
        return False

def message_handler(_, message):
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
            is_closed = kline['x']  # التأكد 100% أن الشمعة أغلقت وانتهت

            if is_closed:
                key = f"{symbol}_{tf}"
                if key not in candle_data:
                    candle_data[key] = []

                # إضافة الشمعة المغلقة
                candle_data[key].append({
                    'open': float(kline['o']),
                    'high': float(kline['h']),
                    'low': float(kline['l']),
                    'close': float(kline['c'])
                })

                # الاحتفاظ بأحدث 5 شموع فقط
                if len(candle_data[key]) > 5:
                    candle_data[key].pop(0)

                stored_count = len(candle_data[key])

                # الفحص يبدأ عند وجود 3 شموع مغلقة ومكتملة تماماً
                if stored_count >= 3:
                    df = pd.DataFrame(candle_data[key])
                    
                    if check_pattern_precise(df):
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print("\n" + "🎯"*30, flush=True)
                        print(f"🚨 [رصد دقيق مؤكد] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}", flush=True)
                        print(f"   📊 إغلاق الخضراء: {kline['c']} | منتصف الحمراء: {(df.iloc[-2]['open']+df.iloc[-2]['close'])/2.0}", flush=True)
                        print("🎯"*30 + "\n", flush=True)
                    else:
                        print(f"🔍 [فحص شمعة مغلقة]: {symbol} ({tf}) - لم تتطابق الشروط.", flush=True)

    except Exception as e:
        pass

def start_radar():
    symbols = [
        "btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", 
        "adausdt", "dogeusdt", "avaxusdt", "dotusdt", "linkusdt"
    ]
    timeframes = ['1m', '3m', '5m', '1h']

    stream_list = [f"{s}@kline_{tf}" for s in symbols for tf in timeframes]

    print("🚀 بدء تشغيل الرادار بالخوارزمية الدقيقة...", flush=True)
    try:
        client = SpotWebsocketStreamClient(on_message=message_handler)
        client.subscribe(stream=stream_list)
        print("✅ تم تفعيل الفحص الدقيق على جميع الفريمات بنجاح!", flush=True)
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}", flush=True)

if __name__ == "__main__":
    start_radar()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
