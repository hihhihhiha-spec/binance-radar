import ccxt
import time
from datetime import datetime
from flask import Flask
import threading

app = Flask(__name__)
# تفعيل الحد من الطلبات لتجنب الحظر من بايننس
exchange = ccxt.binance({'enableRateLimit': True}) 

LIMIT = 250  # عدد مثالي للسيرفر المجاني لضمان عدم التوقف
TIMEFRAMES = ['5m', '15m', '1h', '4h']
history = set()

def is_perfect_pattern(c1, c2):
    # c1: السابقة | c2: الحالية
    # التأكد أن الشموع حمراء
    if c1[4] >= c1[1] or c2[4] >= c2[1]: return False
    
    # حساب الذيول
    upper1, lower1 = (c1[2]-c1[1]), (c1[4]-c1[3])
    upper2, lower2 = (c2[2]-c2[1]), (c2[4]-c2[3])

    # شرطك: الذيل السفلي أطول من العلوي
    if lower1 <= upper1 or lower2 <= upper2: return False
    
    # الشرط الحاسم: الإغلاق تحت "قاع" (ذيل) الشمعة السابقة
    if c2[4] < c1[3]: 
        return True
    return False

def scan_markets():
    try:
        print(f"\n--- 🔄 تبدأ الآن دورة فحص جديدة: {datetime.now().strftime('%H:%M:%S')} ---")
        tickers = exchange.fetch_tickers()
        # اختيار أفضل العملات من حيث السيولة لتجنب العملات "الوهمية"
        symbols = [s for s in tickers.keys() if s.endswith('/USDT')]
        symbols = symbols[:LIMIT]
        
        for index, symbol in enumerate(symbols):
            # طباعة التقدم كل 25 عملة لضمان استمرار تدفق السجلات
            if index % 25 == 0:
                print(f"📡 الرادار يمسح حالياً: {symbol} ({index}/{LIMIT})")
            
            for tf in TIMEFRAMES:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=3)
                    if len(ohlcv) < 3: continue
                    
                    # الفحص بين الشمعة المكتملة (قبل الأخيرة) والتي قبلها
                    if is_perfect_pattern(ohlcv[-3], ohlcv[-2]):
                        alert_id = f"{symbol}_{tf}_{ohlcv[-2][0]}"
                        if alert_id not in history:
                            print(f"\n🎯🎯 صيد ثمين: {symbol} | الفريم: {tf}")
                            print(f"📉 الشرط: إغلاق {ohlcv[-2][4]} تحت ذيل {ohlcv[-3][3]}")
                            history.add(alert_id)
                except: continue
            
            # راحة مجهرية بين كل عملة لمنع استهلاك المعالج 100%
            time.sleep(0.05) 
            
    except Exception as e:
        print(f"⚠️ تنبيه مؤقت: {e}")

def radar_loop():
    while True:
        scan_markets()
        print("😴 دورة انتهت. استراحة 20 ثانية لتبريد السيرفر...")
        time.sleep(20) # أهم سطر لمنع Render من إيقاف الكود

@app.route('/')
def home():
    return f"Radar Status: ACTIVE | Symbols: {LIMIT} | Time: {datetime.now()}"

if __name__ == "__main__":
    # تشغيل الرادار في خيط منفصل
    threading.Thread(target=radar_loop, daemon=True).start()
    # تشغيل Flask
    app.run(host='0.0.0.0', port=10000)
