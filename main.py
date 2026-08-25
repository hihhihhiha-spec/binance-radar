import ccxt
import time
import pandas as pd
from datetime import datetime
import os
import threading
from flask import Flask

# سيرفر وهمي لتشغيل الخدمة على Render بدون خطأ No open ports
app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Radar is Running on Render!", 200

@app.route('/health')
def health():
    return "OK", 200

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

def run_radar():
    """المحرك الرئيسي للرادار الذي يعمل داخل Render"""
    time.sleep(2)
    
    exchange = ccxt.binance({
        'enableRateLimit': True, # منع حظر الـ IP
        'timeout': 15000,
        'options': {'defaultType': 'spot'}
    })

    timeframes = ['1m', '3m', '5m', '1h']
    print("🚀 تم تشغيل الرادار بنجاح على سيرفر Render... جاري الفحص...")

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

                        # عند تحقق الشرط
                        if check_pattern(df):
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print("\n" + "="*60)
                            print(f"🚨 [تم الرصد على Render] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}")
                            print("="*60 + "\n")

                    except ccxt.RateLimitExceeded as e:
                        print(f"🛑 [تنبيه IP]: تم تجاوز معدل الطلبات، جاري الانتظار 10 ثوانٍ... {e}")
                        time.sleep(10)
                    except ccxt.NetworkError as e:
                        print(f"🌐 [خطأ شبكة]: تعذر الاتصال بـ Binance: {e}")
                        time.sleep(2)
                    except Exception as e:
                        print(f"⚠️ [خطأ في العملة {symbol} فريم {tf}]: {e}")
                    
                    time.sleep(0.12) # حماية IP من الحظر

        except Exception as e:
            print(f"❌ [خطأ عام في السكربت]: {e} | جاري إعادة المحاولة خلال 5 ثوانٍ...")
            time.sleep(5)

if __name__ == "__main__":
    # تشغيل الرادار في خلفية السيرفر
    threading.Thread(target=run_radar, daemon=True).start()

    # تشغيل البورت الخاص بموقع Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
