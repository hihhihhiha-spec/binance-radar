import ccxt
import time
import requests
import pandas as pd
from datetime import datetime
import os
import threading
from flask import Flask

# 1. إنشاء سيرفر وهمي لمنصة Render لتفادي خطأ No open ports
app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Radar is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. إعدادات بوت تليجرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ لم يتم ضبط TELEGRAM_TOKEN أو TELEGRAM_CHAT_ID في Secrets/Environment Variables.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ خطأ في إرسال تليجرام: {e}")

def check_pattern(df):
    if df is None or len(df) < 3:
        return False

    prev_candle = df.iloc[-3]
    red_candle = df.iloc[-2]
    green_candle = df.iloc[-1]

    # شمعة حمراء أكبر من التي قبلها وتغلق تحت ذيلها
    is_red = red_candle['close'] < red_candle['open']
    red_body = abs(red_candle['close'] - red_candle['open'])
    prev_body = abs(prev_candle['close'] - prev_candle['open'])
    
    is_bigger = red_body > prev_body
    breaks_lower_tail = red_candle['close'] < prev_candle['low']

    if not (is_red and is_bigger and breaks_lower_tail):
        return False

    # شمعة خضراء تالية تغلق عند نصف الشمعة الحمراء على الأقل
    is_green = green_candle['close'] > green_candle['open']
    red_midpoint = red_candle['open'] - (red_body / 2)
    closes_at_half = green_candle['close'] >= red_midpoint

    return is_green and closes_at_half

def run_radar():
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'timeout': 15000,
        'options': {'defaultType': 'spot'}
    })

    timeframes = ['1m', '3m', '5m', '1h']
    print("🚀 بدء الرادار على Render...")

    while True:
        try:
            markets = exchange.load_markets()
            symbols = [s for s in markets if s.endswith('/USDT') and markets[s].get('active', True)]

            for symbol in symbols:
                for tf in timeframes:
                    try:
                        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
                        if not ohlcv or len(ohlcv) < 3:
                            continue

                        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

                        if check_pattern(df):
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            msg = f"🚨 **[تنبيه رادار Binance]**\n\n🔹 **العملة:** `{symbol}`\n🔹 **الفريم:** `{tf}`\n⏰ **الوقت:** `{now}`"
                            print(msg)
                            send_telegram_alert(msg)

                    except ccxt.RateLimitExceeded as e:
                        print(f"🛑 [تجاوز RateLimit]: {e}")
                        time.sleep(10)
                    except Exception as e:
                        pass
                    
                    time.sleep(0.12)

        except Exception as e:
            print(f"❌ [خطأ عام]: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # تشغيل السيرفر الوهمي في خلفية مستقلة (Thread)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # تشغيل الرادار الأساسي
    run_radar()
