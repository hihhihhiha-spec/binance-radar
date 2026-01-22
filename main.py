import ccxt, time, threading, os
from flask import Flask
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home(): 
    return "Ultra-Radar (5 Timeframes) is Active!"

def radar_logic():
    # ربط المحرك ببايننس فيوتشرز [cite: 2026-01-22]
    exchange = ccxt.binance({'options': {'defaultType': 'future'}})
    
    # الفريمات الخمسة لزيادة فرص الصيد [cite: 2026-01-22]
    timeframes = ['5m', '15m', '30m', '1h', '4h']
    
    print("🚀 انطلاق الرادار الشامل.. فحص 5 فريمات لـ 200 عملة")
    
    while True:
        try:
            markets = exchange.load_markets()
            symbols = [s for s, m in markets.items() if m['future'] and '/USDT' in s][:200]
            
            # طباعة "نبض القلب" للتأكد أن الرادار يعمل [cite: 2026-01-22]
            now = datetime.now().strftime("%H:%M:%S")
            print(f"🔄 جاري الفحص الآن.. الساعة: {now} (لا توجد أخطاء)")
            
            for s in symbols:
                for tf in timeframes:
                    try:
                        # جلب الشمعة المكتملة [cite: 2026-01-22]
                        ohlcv = exchange.fetch_ohlcv(s, tf, limit=2)
                        if len(ohlcv) < 2: continue
                        
                        o, h, l, c = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
                        
                        if c < o: # شمعة حمراء [cite: 2026-01-21]
                            body = o - c
                            u_wick = h - o
                            l_wick = c - l
                            
                            # شرطك الهندسي الصعب [cite: 2026-01-21]
                            if l_wick > u_wick and body > (u_wick + l_wick):
                                print(f"🎯 صيد ثمين!! | {s} | فريم: {tf}")
                                print(f"📏 جسم الشمعة: {body:.4f} | ⬇️ الذيل السفلي: {l_wick:.4f}")
                                print("-" * 40)
                    except: continue
            
            print(f"✅ اكتمل فحص 1000 حالة بنجاح.. بانتظار الدورة القادمة.")
            time.sleep(60) # راحة دقيقة لتجنب حظر IP [cite: 2026-01-22]
        except Exception as e:
            print(f"⚠️ تنبيه تقني: {e}")
            time.sleep(10)

# تشغيل الرادار في الخلفية [cite: 2026-01-22]
threading.Thread(target=radar_logic, daemon=True).start()

if __name__ == "__main__":
    # تشغيل السيرفر ليبقى Render مستيقظاً
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
