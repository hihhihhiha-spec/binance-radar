import ccxt, time, threading
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "Radar is Live"

def start_scanning():
    # الاتصال بمحرك الفيوتشرز [cite: 2026-01-22]
    bot = ccxt.binance({'options': {'defaultType': 'future'}})
    print("🔎 فحص الفيوتشرز بدأ...")
    while True:
        try:
            # قائمة مصغرة للتجربة (BTC, ETH, SOL, AVAX, XRP)
            for s in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 'XRP/USDT']:
                ohlcv = bot.fetch_ohlcv(s, '15m', limit=2)
                o, h, l, c = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
                
                # الشروط: حمراء + جسم أكبر من الذيول + ذيل سفلي أطول من العلوي [cite: 2026-01-21]
                if c < o:
                    body = o - c
                    u_wick = h - o
                    l_wick = c - l
                    if l_wick > u_wick and body > (u_wick + l_wick):
                        print(f"🎯 صيد فيوتشرز: {s} | شمعة مثالية")
            time.sleep(30)
        except: time.sleep(10)

threading.Thread(target=start_scanning, daemon=True).start()
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
