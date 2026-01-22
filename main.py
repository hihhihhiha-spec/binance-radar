import ccxt, time, threading, os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home(): 
    return "Radar 200 is Hunting..."

def radar_logic():
    # الاتصال بفيوتشرز بايننس [cite: 2026-01-22]
    exchange = ccxt.binance({'options': {'defaultType': 'future'}})
    print("🚀 تم تشغيل الرادار العملاق.. فحص 200 عملة فيوتشرز بدأ الآن...")
    
    while True:
        try:
            # جلب كافة عملات الفيوتشرز المتاحة [cite: 2026-01-22]
            markets = exchange.load_markets()
            symbols = [symbol for symbol, market in markets.items() if market['future'] and '/USDT' in symbol]
            symbols = symbols[:200] # تحديد أول 200 عملة سيولة
            
            for s in symbols:
                try:
                    # فحص شمعة الـ 15 دقيقة [cite: 2026-01-22]
                    ohlcv = exchange.fetch_ohlcv(s, '15m', limit=2)
                    if len(ohlcv) < 2: continue
                    
                    o, h, l, c = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
                    
                    # شرط الشمعة الحمراء والذيل السفلي الطويل [cite: 2026-01-21]
                    if c < o:
                        body = o - c
                        u_wick = h - o
                        l_wick = c - l
                        
                        # تطبيق معادلة الجسم أكبر من الذيول والذيل السفلي هو الأطول [cite: 2026-01-21]
                        if l_wick > u_wick and body > (u_wick + l_wick):
                            print(f"🎯 صيد من الـ 200 عملة: {s} | تطابق مثالي!")
                except: continue # في حال فشل جلب عملة واحدة، يكمل الباقي لضمان عدم توقف الدائرة
            
            print("🔄 اكتمل فحص 200 عملة.. استراحة لثوانٍ ثم إعادة الفحص")
            time.sleep(60)
        except Exception as e:
            time.sleep(10)

# تشغيل الرادار في الخلفية
threading.Thread(target=radar_logic, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
