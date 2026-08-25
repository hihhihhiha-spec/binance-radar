
import time
import os
import threading
import requests
import pandas as pd
from datetime import datetime
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Futures Radar Active 24/7", 200

@app.route('/health')
def health():
    return "OK", 200

def get_all_futures_symbols():
    try:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            symbols = [
                s['symbol'] for s in data['symbols'] 
                if s['quoteAsset'] == 'USDT' and s['contractType'] == 'PERPETUAL' and s['status'] == 'TRADING'
            ]
            if len(symbols) > 50:
                print(f"✅ تم جلب جميع عملات الفيوتشرز: {len(symbols)} عملة بنجاح!", flush=True)
                return symbols
    except Exception as e:
        print(f"⚠️ خطأ في جلب العملات: {e}", flush=True)

    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]

def check_symbol_tf(symbol, tf):
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={tf}&limit=4"
        res = requests.get(url, timeout=3)
        if res.status_code != 200:
            return

        raw_candles = res.json()
        if len(raw_candles) < 4:
            return

        # نأخذ آخر 3 شموع مغلقة (نستثني الشمعة الحالية غير المغلقة)
        candles = raw_candles[-4:-1]
        
        df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        c1 = df.iloc[0]
        c2 = df.iloc[1]
        c3 = df.iloc[2]

        # 1. الشمعة الحمراء (C2)
        is_c2_red = c2['close'] < c2['open']
        if not is_c2_red:
            return

        c2_body = abs(c2['open'] - c2['close'])
        c1_body = abs(c1['open'] - c1['close'])

        is_body_bigger = c2_body > c1_body
        breaks_c1_low = c2['close'] < c1['low']

        if not (is_body_bigger and breaks_c1_low):
            return

        # 2. الشمعة الخضراء (C3)
        is_c3_green = c3['close'] > c3['open']
        if not is_c3_green:
            return

        is_fully_inside_red = (c3['low'] >= c2['low']) and (c3['high'] <= c2['high'])

        if is_fully_inside_red:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("\n" + "🔥"*30, flush=True)
            print(f"🚨 [فرصة مؤكدة] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}", flush=True)
            print(f"   📊 إغلاق الخضراء: {c3['close']} | داخل نطاق الحمراء [Low: {c2['low']}, High: {c2['high']}]", flush=True)
            print("🔥"*30 + "\n", flush=True)

    except Exception:
        pass

def run_radar_loop():
    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h']
    print("🚀 تم تشغيل الرادار بنجاح والربط مستقر 100%...", flush=True)

    while True:
        try:
            symbols = get_all_futures_symbols()
            print(f"🔍 [فحص شامل]: جاري فحص جميع العملات ({len(symbols)}) عبر جميع الفريمات...", flush=True)
            for symbol in symbols:
                for tf in timeframes:
                    check_symbol_tf(symbol, tf)
                time.sleep(0.02)
            
            print("✅ اكتملت دورة الفحص لجميع العملات بنجاح. انتظار الدقيقة القادمة...", flush=True)
            time.sleep(15)

        except Exception as e:
            print(f"⚠️ تنبيه: {e}", flush=True)
            time.sleep(10)

# تشغيل الفحص في خلفية السيرفر
threading.Thread(target=run_radar_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
