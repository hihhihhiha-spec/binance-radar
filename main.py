import sys
import time
import os
import threading
import requests
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- تفعيل الطباعة الفورية الإجبارية ---
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

print("==================================================", flush=True)
print("🟢 [اختبار إجباري] بدأ تشغيل السكريبت الآن بنجاح تام!", flush=True)
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
    print(f"🌐 خادم الويب يعمل على البورت: {port}", flush=True)
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

def main():
    print("🟢 [دالة المين الرئيسية تعمل] جاري البدء...", flush=True)
    send_telegram_message("🟢 تم إعادة تشغيل البوت بنجاح والتأكد من عمل الطباعة.")

    while True:
        print("🔄 [فحص تجريبي] البوت يعمل ويقوم بالدورة الآن...", flush=True)
        time.sleep(10)

if __name__ == "__main__":
    main()
