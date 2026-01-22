import ccxt
import time
from datetime import datetime
from flask import Flask
import threading

app = Flask(__name__)
# استخدام مكتبة pro لزيادة سرعة جلب البيانات
exchange = ccxt.binance({'enableRateLimit': False}) 

SYMBOLS_LIMIT = 500 
TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h']
history = set()

def is_perfect_pattern(c1, c2):
    # c1 السابقة، c2 الحالية
    # التأكد أنها حمراء
    if c1[4] >= c1[1] or c2[4] >= c2[1]: return False
    
    # حساب الذيول
    upper1, lower1 = (c1[2]-c1[1]), (c1[4]-c1[3])
    upper2, lower2 = (c2[2]-c2[1]), (c2[4]-c2[3])

    # شرطك الأساسي: الذيل السفلي أكبر من العلوي للشمعتين
    if lower1 <= upper1 or lower2 <= upper2: return False
    
    # شرط الكسر: إغلاق الثانية تحت ذيل الأولى
    if c2[4] < c1[3]:
        return True
    return False

def scan_markets():
    print(f"⚡ جاري المسح الشامل لـ {SYMBOLS_LIMIT} عملة.. {datetime.now().strftime('%H:%M:%S')}")
    try:
        tickers = exchange.fetch_tickers()
        symbols = [s for s in tickers.keys() if s.endswith('/USDT')][:SYMBOLS_LIMIT]
        
        for symbol in symbols:
            # طباعة نقطة لكل عملة لتعرف أن الكود "يطير" ولا يتوقف
            for tf in TIMEFRAMES:
                try:
                    # طلب الحد الأدنى من البيانات لزيادة السرعة
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=3)
                    if len(ohlcv) < 3: continue
                    if is_perfect_pattern(ohlcv[-3], ohlcv[-2]):
                        alert_id = f"{symbol}_{tf}_{ohlcv[-2][0]}"
                        if alert_id not in history:
                            print(f"🎯 صيد! {symbol} | {tf} | كسر + ذيل سفلي طويل ✅")
                            history.add(alert_id)
                except: continue
    except Exception as e:
        print(f"⚠️ خطأ مؤقت: {e}")

def radar_loop():
    while True:
        scan_markets()
        if len(history) > 1000: history.clear()
        time.sleep(1) # العودة للفحص فوراً دون انتظار

@app.route('/')
def home():
    return "<h1>الرادار السريع يعمل...</h1>"

if __name__ == "__main__":
    threading.Thread(target=radar_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
