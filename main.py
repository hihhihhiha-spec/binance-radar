import ccxt, time, threading
from flask import Flask

# إعداد السيرفر ليتوافق مع Render
app = Flask(__name__)
@app.route('/')
def home(): return "Radar Active"

def radar_logic():
    # الاتصال بفيوتشرز بايننس حصراً [cite: 2026-01-22]
    exchange = ccxt.binance({'options': {'defaultType': 'future'}})
    while True:
        try:
            # قائمة عملات الفيوتشرز الأساسية
            for s in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 'XRP/USDT']:
                ohlcv = exchange.fetch_ohlcv(s, '15m', limit=2)
                o, h, l, c = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
                
                # شرط الشمعة الحمراء والذيل السفلي الأطول [cite: 2026-01-21]
                if c < o:
                    body, u_wick, l_wick = (o - c), (h - o), (c - l)
                    if l_wick > u_wick and body > (u_wick + l_wick):
                        print(f"🎯 صيد فيوتشرز: {s} | شمعة مثالية")
            time.sleep(30)
        except: time.sleep(10)

# تشغيل الرادار في الخلفية
threading.Thread(target=radar_logic, daemon=True).start()

if __name__ == "__main__":
    # استخدام المنفذ الذي يطلبه Render في صورك
    app.run(host='0.0.0.0', port=10000)
