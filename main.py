import ccxt, time, threading
from flask import Flask

app = Flask(__name__)
@app.route('/')
def health(): return "OK"

def radar():
    ex = ccxt.binance({'options': {'defaultType': 'future'}}) # سوق الفيوتشرز [cite: 2026-01-22]
    while True:
        try:
            # فحص أهم 50 عملة فيوتشرز لسرعة الأداء
            symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 'XRP/USDT', 'ADA/USDT'] 
            for s in symbols:
                ohlcv = ex.fetch_ohlcv(s, '15m', limit=2)
                o, h, l, c = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
                
                # شرطك: شمعة حمراء + ذيل سفلي أطول من العلوي + جسم صلب [cite: 2026-01-21]
                if c < o:
                    body, u_wick, l_wick = (o - c), (h - o), (c - l)
                    if l_wick > u_wick and body > (u_wick + l_wick):
                        print(f"🎯 صيد فيوتشرز: {s} | شمعة مثالية")
            time.sleep(30)
        except: time.sleep(10)

threading.Thread(target=radar, daemon=True).start()
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
