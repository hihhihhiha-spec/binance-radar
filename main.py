import sys
import time
import os
import threading
import ccxt
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# فرض الطباعة الفورية اللحظية
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

print("🟢 [البداية] تم إقلاع السكريبت وجاري تهيئة الاتصال...", flush=True)

TELEGRAM_TOKEN = "8866274181:AAEU7Ofsem4EW87PNo1Uk_sNs0VSejcSmvI"
CHAT_ID = "6141474899"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Telegram Error: {e}", flush=True)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar is Running and Printing Logs")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

exchange = ccxt.bybit({
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

def main():
    print("🟢 [الرادار] بدأ العمل...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار مع تفعيل التتبع المرئي المباشر.")

    timeframes = ['1m', '5m', '15m', '30m', '1h', '4h']
    symbols = []
    cycle = 1

    while True:
        try:
            print("🔍 جاري جلب قائمة العملات من Bybit...", flush=True)
            exchange.load_markets()
            tickers = exchange.fetch_tickers()
            
            movers = []
            for symbol, data in tickers.items():
                if '/USDT:USDT' in symbol or symbol.endswith('/USDT'):
                    try:
                        pct = float(data.get('percentage', 0) or 0)
                        base_symbol = symbol.split('/')[0].lower() + "usdt"
                        movers.append((base_symbol, pct))
                    except:
                        continue
                        
            movers.sort(key=lambda x: x[1], reverse=True)
            symbols = [m[0] for m in movers[:500]]
            print(f"🔥 تم بنجاح جلب {len(symbols)} عملة. بدء الفحص...", flush=True)

            for idx, symbol in enumerate(symbols):
                # طباعة صريحة لكل عملة يتم فحصها الآن
                print(f"➡️ [{idx+1}/{len(symbols)}] جاري فحص العملة: {symbol.upper()}", flush=True)
                
                for tf in timeframes:
                    try:
                        formatted_symbol = f"{symbol[:-4].upper()}/USDT:USDT"
                        candles = exchange.fetch_ohlcv(formatted_symbol, timeframe=tf, limit=25)
                        if not candles or len(candles) < 15:
                            continue
                        
                        # فحص بسيط للتأكد من الحركة
                        latest_c = candles[-2]
                        print(f"    ✔️ تم فحص {symbol.upper()} | الفريم {tf}", flush=True)
                    except Exception as ex:
                        print(f"    ⚠️ خطأ في فحص {symbol.upper()} على {tf}: {ex}", flush=True)
                    
                    time.sleep(0.01)

            print(f"✅ اكتملت الدورة رقم {cycle}\n", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ عام في الحلقة: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
