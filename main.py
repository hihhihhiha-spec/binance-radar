import ccxt
import time
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

def play_radar_sound():
    try:
        if sys.platform == "win32":
            import winsound
            for _ in range(3):
                winsound.Beep(2000, 300)
                time.sleep(0.05)
        elif sys.platform == "darwin":
            os.system('say "Alert"')
        else:
            print('\a', flush=True)
    except Exception:
        print('\a', flush=True)

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar Active")
    def log_message(self, format, *args): return

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_port_server, daemon=True).start()

# إعداد الاتصال
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

MY_SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'DOGE/USDT', 'PEPE/USDT']
TIMEFRAMES = ['5m', '15m', '1h']

detected_signals = set()

def check_logic(symbol, tf):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
        if not bars or len(bars) < 3: 
            return False
        
        c1, c2 = bars[-3], bars[-2]
        o1, h1, l1, cl1, t1 = c1[1], c1[2], c1[3], c1[4], c1[0]
        o2, h2, l2, cl2, t2 = c2[1], c2[2], c2[3], c2[4], c2[0]

        is_red1 = cl1 < o1
        is_red2 = cl2 < o2
        broken_low = l2 < l1

        body2 = o2 - cl2
        total_range2 = h2 - l2
        
        # تخفيف شرط الجسم: أن يمثل الجسم 40% على الأقل من طول الشمعة الكلي
        strong_body2 = (body2 / total_range2) >= 0.4 if total_range2 > 0 else False

        # طباعة تشخيصية فقط لزوج BTC لتوضيح السبب
        if symbol == 'BTC/USDT' and tf == '5m':
            print(f"\n[تشخيص BTC 5m] حمراء1: {is_red1} | حمراء2: {is_red2} | كسر القاع: {broken_low} | نسبة الجسم: {round((body2/total_range2)*100 if total_range2 else 0)}%", flush=True)

        if is_red1 and is_red2 and broken_low and strong_body2:
            signal_id = f"{symbol}_{tf}_{t2}"
            if signal_id not in detected_signals:
                detected_signals.add(signal_id)
                return True

        return False
    except Exception as e:
        print(f"خطأ في {symbol}: {e}", flush=True)
        return False

print("🚀 بدء تشغيل الرادار الاختباري...", flush=True)

while True:
    try:
        for index, symbol in enumerate(MY_SYMBOLS, 1):
            for tf in TIMEFRAMES:
                if check_logic(symbol, tf):
                    print(f"\n🎯🎯 تم الصيد: {symbol} | الفريم: {tf} 🎯🎯\n", flush=True)
                    play_radar_sound()
            time.sleep(0.1)
        print("--- نهاية الدورة ---", flush=True)
        time.sleep(5)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(10)
