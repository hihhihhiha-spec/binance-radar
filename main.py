import ccxt
import time
from datetime import datetime
from flask import Flask
import threading

app = Flask(__name__)
exchange = ccxt.binance()

# إعدادات النسخة القصوى
SYMBOLS_LIMIT = 500  # رفع العدد لـ 500 عملة لجلب نتائج أكثر
TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h']
history = set()

def is_perfect_pattern(c1, c2):
    # c1 السابقة، c2 الحالية
    # [timestamp, open, high, low, close, volume]
    if c1[4] >= c1[1] or c2[4] >= c2[1]: return False # يجب أن تكون حمراء
    
    # الشرط الأساسي: إغلاق الثانية تحت ذيل الأولى
    cond_break = c2[4] < c1[3] 
    
    # شرط الذيول: الذيل السفلي أكبر من العلوي في الشمعتين
    lower_wick1 = c1[4] - c1[3]
    upper_wick1 = c1[2] - c1[1]
    lower_wick2 = c2[4] - c2[3]
    upper_wick2 = c2[2] - c2[1]
    
    cond_wicks = lower_wick1 > upper_wick1 and lower_wick2 > upper_wick2
    
    if cond_break and cond_wicks:
        return True
    return False

def scan_markets():
    now = datetime.now().strftime('%H:%M:%S')
    print(f"🚀 [نظام الفحص] جاري مسح {SYMBOLS_LIMIT} عملة عبر 7 فريمات.. الساعة الآن: {now}")
    
    try:
        tickers = exchange.fetch_tickers()
        all_symbols = [s for s in tickers.keys() if s.endswith('/USDT')]
        symbols = all_symbols[:SYMBOLS_LIMIT]
        
        found_in_round = 0
        for symbol in symbols:
            # رسالة نبض كل 50 عملة لتعرف أن الفحص مستمر
            if symbols.index(symbol) % 50 == 0:
                print(f"⏳ معالجة الدفعة رقم {symbols.index(symbol)//50 + 1}...")

            for tf in TIMEFRAMES:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=3)
                    if len(ohlcv) < 3: continue
                    
                    c1, c2 = ohlcv[-3], ohlcv[-2]
                    
                    if is_perfect_pattern(c1, c2):
                        alert_id = f"{symbol}_{tf}_{c2[0]}"
                        if alert_id not in history:
                            print(f"🎯 صيد ثمين! {symbol} | فريم: {tf} | كسر هابط محقق ✅")
                            history.add(alert_id)
                            found_in_round += 1
                except: continue
        
        print(f"✅ اكتملت الدورة. تم إيجاد {found_in_round} فرصة جديدة.")
        
    except Exception as e:
        print(f"❌ تنبيه: حدث بطء في الاتصال، سأحاول مجدداً.. ({e})")

def radar_loop():
    while True:
        scan_markets()
        if len(history) > 2000: history.clear()
        time.sleep(10) # فحص متكرر سريع جداً

@app.route('/')
def home():
    return f"<h1>رادار الـ 500 عملة يعمل بنجاح! الوقت: {datetime.now()}</h1>"

if __name__ == "__main__":
    threading.Thread(target=radar_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
