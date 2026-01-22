import requests
import time
import http.server
import threading

# --- إضافة كود لخداع السيرفر لكي لا يتوقف ---
def start_dummy_server():
    server_address = ('', 10000)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# تشغيل السيرفر الوهمي في خلفية الكود
threading.Thread(target=start_dummy_server, daemon=True).start()

# --- كود الرادار الخاص بك ---
timeframes = ['5m', '15m', '1h', '4h']

def get_all_symbols():
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        res = requests.get(url, timeout=10).json()
        return [s['symbol'] for s in res if s['symbol'].endswith('USDT')][:250]
    except: return ["BTCUSDT", "ETHUSDT"]

def start_scanning():
    symbols = get_all_symbols()
    print(f"✅ الرادار بدأ العمل بنجاح عالمياً...")
    while True:
        for tf in timeframes:
            print(f"🔍 فحص {tf}...")
            for s in symbols:
                try:
                    url = "https://api.binance.com/api/v3/klines"
                    params = {'symbol': s, 'interval': tf, 'limit': 3}
                    data = requests.get(url, params=params).json()
                    p_o, p_c = float(data[-3][1]), float(data[-3][4])
                    c_o, c_c = float(data[-2][1]), float(data[-2][4])
                    if c_c < c_o and p_c < p_o: # شرط الشمعتين الحمراوين
                        print(f"🎯 فرصة لقطة: {s} ({tf})")
                    time.sleep(0.05)
                except: continue
        time.sleep(60)

if __name__ == "__main__":
    start_scanning()
