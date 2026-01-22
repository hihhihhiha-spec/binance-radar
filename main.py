import requests
import time

timeframes = ['5m', '15m', '1h', '4h']

def get_all_symbols():
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        res = requests.get(url, timeout=10).json()
        symbols = [s['symbol'] for s in res if s['symbol'].endswith('USDT')]
        return symbols[:250]
    except:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def start_scanning():
    symbols = get_all_symbols()
    print(f"✅ تم الاتصال بنجاح. جاري فحص {len(symbols)} عملة عالمية...")

    while True:
        for tf in timeframes:
            print(f"🔍 فحص إطار {tf} الآن...")
            for s in symbols:
                try:
                    url = "https://api.binance.com/api/v3/klines"
                    params = {'symbol': s, 'interval': tf, 'limit': 3}
                    data = requests.get(url, params=params, timeout=5).json()
                    if not data or len(data) < 3: continue
                    p_o, p_h, p_l, p_c = float(data[-3][1]), float(data[-3][2]), float(data[-3][3]), float(data[-3][4])
                    c_o, c_h, c_l, c_c = float(data[-2][1]), float(data[-2][2]), float(data[-2][3]), float(data[-2][4])
                    def is_perfect_candle(o, h, l, c):
                        body = abs(o - c)
                        tails = (h - max(o, c)) + (min(o, c) - l)
                        return c < o and body > tails
                    if is_perfect_candle(p_o, p_h, p_l, p_c) and is_perfect_candle(c_o, c_h, c_l, c_c):
                        if c_l < p_l:
                            print(f"🎯 [لقطة هبوط] {s} | فريم {tf} | السعر: {c_c}")
                    time.sleep(0.05)
                except: continue
        print("💤 دورة فحص كاملة انتهت. انتظار دقيقتين...")
        time.sleep(120)

if __name__ == "__main__":
    start_scanning()
