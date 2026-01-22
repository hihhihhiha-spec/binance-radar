import ccxt, time, threading, os
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "Radar is Online!"

def radar():
    # الاتصال المباشر بفيوتشرز بايننس لضمان دقة الذيول [cite: 2026-01-22]
    exchange = ccxt.binance({'options': {'defaultType': 'future'}})
    print("✅ تم تشغيل المحرك.. جاري البحث عن الفرص...")
    
    while True:
        try:
            # سنفحص عملتين فقط للتأكد من سرعة الاستجابة في البداية
            for s in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
                print(f"🔍 أفحص الآن: {s}") 
                ohlcv = exchange.fetch_ohlcv(s, '15m', limit=2)
                o, h, l, c = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
                
                if c < o: # شمعة حمراء [cite: 2026-01-21]
                    body, u_wick, l_wick = (o - c), (h - o), (c - l)
                    # شرطك: ذيل سفلي أطول من العلوي + جسم صلب [cite: 2026-01-21]
                    if l_wick > u_wick and body > (u_wick + l_wick):
                        print(f"🎯 صيد ثمين وجدته لك: {s} | شمعة حمراء بذيول مثالية")
            time.sleep(10)
        except Exception as e:
            print(f"❌ حدث خطأ بسيط: {e}")
            time.sleep(5)

threading.Thread(target=radar, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
