import ccxt
import time
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- 0. دالة الصوت التنبيهي ---
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

# --- 1. خادم منع التوقف السحابي ---
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

# --- 2. إعدادات بينانس مع تفعيل حماية الحد الأقصى للطلبات ---
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,  # منع تجاوز حدود باينانس
    'timeout': 30000
})

MY_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'LTC/USDT',
    'NEAR/USDT', 'OP/USDT', 'ARB/USDT', 'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT',
    'TIA/USDT', 'SEI/USDT', 'SUI/USDT', 'APT/USDT', 'HBAR/USDT', 'FIL/USDT', 'ICP/USDT', 'INJ/USDT', 'RNDR/USDT', 'FET/USDT'
]

# تقليل الأطر الزمنية لتقليل ضغط الطلبات ومنع الحظر
TIMEFRAMES = ['15m', '1h', '4h']

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
        
        # جسم الشمعة يشكل 45% على الأقل من طولها
        strong_body2 = (body2 / total_range2) >= 0.45 if total_range2 > 0 else False

        if is_red1 and is_red2 and broken_low and strong_body2:
            signal_id = f"{symbol}_{tf}_{t2}"
            if signal_id not in detected_signals:
                detected_signals.add(signal_id)
                return True

        return False
    except ccxt.RateLimitExceeded:
        print("⚠️ تحذير: اقتراب من حد الطلبات، سيتم الانتظار قليلاً...", flush=True)
        time.sleep(10)
        return False
    except Exception:
        return False

print(f"🚀 تم تشغيل الرادار بحماية من الحظر ({len(MY_SYMBOLS)} عملة)...", flush=True)

while True:
    try:
        for index, symbol in enumerate(MY_SYMBOLS, 1):
            for tf in TIMEFRAMES:
                if check_logic(symbol, tf):
                    print(f"\n🎯 ALERT: {symbol} | TF: {tf}\n", flush=True)
                    play_radar_sound()
                time.sleep(0.2) # تأخير آمن لمنع حظر الـ IP
                
        print(f"[{datetime.now().strftime('%H:%M:%S')}] اكتملت الدورة. إراحة 15 ثانية...", flush=True)
        time.sleep(15)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(30)
