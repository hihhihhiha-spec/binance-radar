import ccxt
import time
from datetime import datetime
from flask import Flask
import threading

app = Flask(__name__)
# تفعيل أقصى سرعة جلب بيانات
exchange = ccxt.binance({'enableRateLimit': False}) 

SYMBOLS_LIMIT = 500 
TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h'] # ركزنا على الفريمات السريعة لتقليل وقت الانتظار
history = set()

def is_perfect_pattern(c1, c2):
    # الحفاظ على استراتيجيتك الأصلية بدقة 100%
    if c1[4] >= c1[1] or c2[4] >= c2[1]: return False
    upper1, lower1 = (c1[2]-c1[1]), (c1[4]-c1[3])
    upper2, lower2 = (c2[2]-c2[1]), (c2[4]-c2[3])
    # شرط الذيول السفلية أكبر من العلوية
    if lower1 <= upper1 or lower2 <= upper2: return False
    # شرط كسر قاع الشمعة السابقة
    if c2[4] < c1[3]: return True
    return False

def scan_markets():
    now_str = datetime.now().strftime('%H:%M:%S')
    print(f"🚀 بدأت دورة فحص جديدة لـ {SYMBOLS_LIMIT} عملة.. الساعة: {now_str}")
    try:
        tickers = exchange.fetch_tickers()
        symbols = [s for s in tickers.keys() if s.endswith('/USDT')][:SYMBOLS_LIMIT]
        
        for index, symbol in enumerate(symbols):
            # طباعة اسم العملة فوراً لتعرف أين وصل الرادار الآن
            print(f"🔍 فحص: {symbol} ({index+1}/{SYMBOLS_LIMIT})", end='\r')
            
            for tf in TIMEFRAMES:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=3)
                    if len(ohlcv) < 3: continue
                    if is_perfect_pattern(ohlcv[-3], ohlcv[-2]):
                        alert_id = f"{symbol}_{tf}_{ohlcv[-2][0]}"
                        if alert_id not in history:
                            # طباعة النتيجة فوراً بسطر منفصل
                            print(f"\n🎯 صيد ثمين! {symbol} | فريم: {tf} | كسر + ذيل سفلي طويل ✅")
                            history.add(alert_id)
                except: continue
        print(f"\n✅ انتهى فحص الـ 500 عملة بنجاح.")
    except Exception as e:
        print(f"\n⚠️ تنبيه: {e}")

def radar_loop():
    while True:
        scan_markets()
        if len(history) > 1000: history.clear()
        time.sleep(1)

@app.route('/')
def home():
    return "<h1>الرادار اللحظي يعمل...</h1>"

if __name__ == "__main__":
    threading.Thread(target=radar_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
