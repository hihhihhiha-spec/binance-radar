import ccxt
import time
from flask import Flask
import threading

# إعداد سيرفر وهمي لإبقاء الخدمة تعمل على Render
app = Flask('')
@app.route('/')
def home(): return "Radar is Running!"

def run_radar():
    # الاتصال بسوق الفيوتشرز في بايننس
    exchange = ccxt.binance({'options': {'defaultType': 'future'}})
    print("🚀 انطلاق رادار الفيوتشرز المطور...")
    
    while True:
        try:
            # جلب كل عملات الفيوتشرز المتاحة مقابل USDT
            markets = exchange.fetch_markets()
            symbols = [m['symbol'] for m in markets if m['active'] and m['linear'] and m['quote'] == 'USDT']
            
            for tf in ['5m', '15m', '1h', '4h']:
                print(f"🔍 فحص إطار {tf}...")
                for sym in symbols:
                    try:
                        ohlcv = exchange.fetch_ohlcv(sym, tf, limit=2)
                        if len(ohlcv) < 2: continue
                        
                        # الشمعة السابقة (المكتملة)
                        o, h, l, c = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
                        
                        # 1. شرط اللون: شمعة حمراء
                        if c < o:
                            body = o - c
                            upper_wick = h - o
                            lower_wick = c - l
                            
                            # 2. شرط الذيول: السفلي أطول من العلوي + الجسم أكبر من الذيول
                            if lower_wick > upper_wick and body > (upper_wick + lower_wick):
                                print(f"🎯 صيد فيوتشرز: {sym} ({tf}) - ذيل سفلي طويل")
                    except: continue
                    time.sleep(0.1) # سرعة الفحص
            
            print("💤 انتهاء الدورة. انتظار دقيقة...")
            time.sleep(60)
        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(10)

# تشغيل الرادار في الخلفية
threading.Thread(target=run_radar).start()
app.run(host='0.0.0.0', port=10000)
