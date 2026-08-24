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

# --- 1. خادم منع توقف السيرفر (Render Keeper) ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar is Active")
    def log_message(self, format, *args): return

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_port_server, daemon=True).start()

# --- 2. إعدادات باينانس ---
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
    'timeout': 15000
})

TIMEFRAMES = ['5m', '15m', '1h']
alerted_candles = set()

# --- 3. جلب أعلى 100 عملة سيولة تلقائياً ---
def fetch_top_100_symbols():
    try:
        tickers = exchange.fetch_tickers()
        usdt_pairs = [
            (symbol, data['quoteVolume']) 
            for symbol, data in tickers.items() 
            if symbol.endswith('/USDT') and data.get('quoteVolume') is not None
        ]
        # ترتيب العملات حسب حجم التداول (السيولة) من الأعلى للأقل
        usdt_pairs.sort(key=lambda x: x[1], reverse=True)
        top_100 = [item[0] for item in usdt_pairs[:100]]
        print(f"✅ تم تجديد قائمة أعلى 100 عملة سيولة بنجاح.", flush=True)
        return top_100
    except Exception as e:
        print(f"⚠️ خطأ أثناء جلب قائمة السيولة: {e}", flush=True)
        return []

# --- 4. فحص الشمعة الحمراء الحية ---
def check_live_red_candle(symbol, tf):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=2)
        if not bars:
            return False, 0

        current_candle = bars[-1]
        candle_timestamp = current_candle[0]
        open_price = current_candle[1]
        close_price = current_candle[4]

        # فحص إن كانت الشمعة الحية حمراء
        if close_price < open_price:
            return True, candle_timestamp

        return False, 0
    except ccxt.RateLimitExceeded:
        print("⚠️ تجاوز حد الطلبات، انتظار مؤقت...", flush=True)
        time.sleep(5)
        return False, 0
    except Exception:
        return False, 0

print(f"🚀 بدء الرادار المباشر لأعلى 100 عملة سيولة...", flush=True)

active_symbols = []

while True:
    try:
        # تجديد القائمة في بداية كل دورة أو عند فراغها
        if not active_symbols:
            active_symbols = fetch_top_100_symbols()
            if not active_symbols:
                time.sleep(15)
                continue

        print(f"[{datetime.now().strftime('%H:%M:%S')}] بدء دورة الفحص لـ {len(active_symbols)} عملة...", flush=True)

        for index, symbol in enumerate(active_symbols, 1):
            for tf in TIMEFRAMES:
                is_red, c_time = check_live_red_candle(symbol, tf)
                
                if is_red:
                    alert_id = f"{symbol}_{tf}_{c_time}"
                    if alert_id not in alerted_candles:
                        alerted_candles.add(alert_id)
                        print(f"\n🔥 [تنبيه مباشر] {symbol} | شمعة حمراء حية! | الفريم: {tf} | الوقت: {datetime.now().strftime('%H:%M:%S')}\n", flush=True)
                        play_radar_sound()

                # تأخير آمن لمنع حظر الـ IP
                time.sleep(0.06)

        # تنظيف سجل التنبيهات إذا زاد حجمه
        if len(alerted_candles) > 1000:
            alerted_candles.clear()

        # تجديد قائمة السيولة تلقائياً في نهاية الدورة
        active_symbols = fetch_top_100_symbols()
        time.sleep(5)

    except Exception as e:
        print(f"خطأ غير متوقع: {e}", flush=True)
        time.sleep(10)
