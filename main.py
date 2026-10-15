import sys
import time
import os
import threading
import ccxt
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- فرض الطباعة الفورية القصوى ---
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

print("==================================================", flush=True)
print("🟢 [اختبار فوري] بدأ تشغيل السكريبت الآن...", flush=True)
print("==================================================", flush=True)

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
        self.wfile.write(b"Test Radar is Active")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# إعداد CCXT
exchange = ccxt.bybit({
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

def main():
    print("🟢 [دالة المين] جاري جلب الأسواق عبر CCXT...", flush=True)
    send_telegram_message("🟢 بدأ اختبار الرادار الحي على Render.")

    while True:
        try:
            print("🔍 جاري جلب العملات...", flush=True)
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
            top_symbols = [m[0] for m in movers[:5]] # أخذ أول 5 عملات فقط للاختبار السريع
            
            print(f"🔥 تم بنجاح جلب العملات! أول 5 عملات هي: {top_symbols}", flush=True)

            for symbol in top_symbols:
                print(فحص العملة: {symbol.upper()}, flush=True)
                # جلب الشموع للتأكد
                formatted_symbol = f"{symbol[:-4].upper()}/USDT:USDT"
                candles = exchange.fetch_ohlcv(formatted_symbol, timeframe='1h', limit=10)
                print(f"    ✅ تم جلب {len(candles)} شمعة للعملة {symbol.upper()}", flush=True)
                time.sleep(1)

            print("⏳ انتهت دورة الاختبار، ستبدأ من جديد بعد 10 ثوانٍ...\n", flush=True)
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ خطأ أثناء التشغيل: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
