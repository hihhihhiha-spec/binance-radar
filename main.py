import ccxt
import time
from datetime import datetime
from flask import Flask
import threading

app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': False}) 

SYMBOLS_LIMIT = 500 
TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h']
history = set()

def is_perfect_pattern(c1, c2):
    # c1 السابقة، c2 الحالية
    # [timestamp, open, high, low, close, volume]
    
    # 1. التأكد أن الشموع حمراء
    if c1[4] >= c1[1] or c2[4] >= c2[1]: return False
    
    # 2. حساب الذيول
    upper1, lower1 = (c1[2]-c1[1]), (c1[4]-c1[3])
    upper2, lower2 = (c2[2]-c2[1]), (c2[4]-c2[3])

    # 3. شرطك: الذيل السفلي أكبر من العلوي للشمعتين
    if lower1 <= upper1 or lower2 <= upper2: return False
    
    # 4. الشرط الجوهري: إغلاق الشمعة الحالية (c2) تحت "أدنى سعر" (ذيل) السابقة (c1)
    if c2[4] < c1[3]: 
        return True
    return False

def scan_markets():
    now_str = datetime.now().strftime('%H:%M:%S')
    print(f"🚀 دورة جديدة: فحص {SYMBOLS_LIMIT} عملة... الوقت: {now_str}")
    try:
        tickers = exchange.fetch_tickers()
        symbols = [s for s in tickers.keys() if s.endswith('/USDT')][:SYMBOLS_LIMIT]
        
        for index, symbol in enumerate(symbols):
            # يطبع رسالة كل 50 عملة لضمان عدم تجمد الشاشة (Buffer)
            if index % 50 == 0:
                print(f"⏳ الرادار نشط.. يفحص الآن العملة رقم {index} ({symbol})")
            
            for tf in TIMEFRAMES:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=3)
                    if len(ohlcv) < 3: continue
                    
                    # الفحص (c1 هي السابقة ohlcv[-3] و c2 هي الحالية ohlcv[-2])
                    if is_perfect_pattern(ohlcv[-3], ohlcv[-2]):
                        alert_id = f"{symbol}_{tf}_{ohlcv[-2][0]}"
                        if alert_id not in history:
                            print(f"\n🎯🎯🎯 صيد ثمين!! {symbol} | فريم: {tf}")
                            print(f"✅ الإغلاق تحت الذيل السابق محقق")
                            history.add(alert_id)
                except: continue
                
    except Exception as e:
        print(f"⚠️ تنبيه: {e}")

def radar_loop():
    while True:
        scan_markets()
        time.sleep(2) # راحة بسيطة لضمان استقرار السيرفر

@app.route('/')
def home():
    return f"Radar Active - Last Check: {datetime.now()}"

if __name__ == "__main__":
    threading.Thread(target=radar_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
