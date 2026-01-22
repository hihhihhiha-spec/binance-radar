import ccxt
import time
from datetime import datetime
from flask import Flask
import threading

app = Flask(__name__)
exchange = ccxt.binance()

# إعدادات الرادار المتطورة
SYMBOLS_LIMIT = 300 
TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h']
history = set() # ذاكرة منع التكرار

def is_perfect_pattern(c1, c2):
    # c1 هي الشمعة السابقة، c2 هي الشمعة الحالية
    # البيانات: [timestamp, open, high, low, close, volume]
    
    # 1. التأكد أن الشمعتين حمراء
    if c1[4] >= c1[1] or c2[4] >= c2[1]: return False
    
    # حسابات الشمعة الأولى (c1)
    body1 = c1[1] - c1[4]
    upper_wick1 = c1[2] - c1[1]
    lower_wick1 = c1[4] - c1[3]
    
    # حسابات الشمعة الثانية (c2)
    body2 = c2[1] - c2[4]
    upper_wick2 = c2[2] - c2[1]
    lower_wick2 = c2[4] - c2[3]

    # الشرط: الجسم أكبر من الذيول (ممتلئة) والذيل السفلي أطول من العلوي
    cond_full1 = body1 > (upper_wick1 + lower_wick1) and lower_wick1 > upper_wick1
    cond_full2 = body2 > (upper_wick2 + lower_wick2) and lower_wick2 > upper_wick2
    
    # الشرط الجوهري: الشمعة الثانية تكسر وتغلق تحت ذيل الشمعة الأولى
    cond_break = c2[4] < c1[3] 
    
    if cond_full1 and cond_full2 and cond_break:
        return True
    return False

def scan_markets():
    print(f"🔄 فحص 2100 حالة.. {datetime.now().strftime('%H:%M:%S')}")
    try:
        tickers = exchange.fetch_tickers()
        symbols = [s for s in tickers.keys() if s.endswith('/USDT')][:SYMBOLS_LIMIT]
        
        for symbol in symbols:
            for tf in TIMEFRAMES:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=3)
                    if len(ohlcv) < 3: continue
                    
                    # نأخذ آخر شمعتين مكتملتين
                    c1, c2 = ohlcv[-3], ohlcv[-2]
                    
                    if is_perfect_pattern(c1, c2):
                        alert_id = f"{symbol}_{tf}_{c2[0]}" # معرف فريد لمنع التكرار
                        if alert_id not in history:
                            print(f"🎯 صيد ثمين! {symbol} | فريم: {tf} | كسر وإغلاق هابط")
                            history.add(alert_id)
                except: continue
    except Exception as e:
        print(f"❌ خطأ: {e}")

def radar_loop():
    while True:
        scan_markets()
        # تنظيف الذاكرة إذا كبرت جداً
        if len(history) > 1000: history.clear()
        time.sleep(20) # فحص سريع جداً كل 20 ثانية

@app.route('/')
def home():
    return "<h1>رادار الكسر المزدوج يعمل بـ 300 عملة...</h1>"

if __name__ == "__main__":
    threading.Thread(target=radar_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
