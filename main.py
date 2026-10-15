import sys
import time
import os
import threading
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- تفعيل الطباعة الفورية القصوى ---
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

print("🚀 [بدء التشغيل] السكريبت يعمل الآن...", flush=True)

# خادم الويب لـ Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar is Running Perfectly")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 خادم الويب يفتح على البورت: {port}", flush=True)
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# تشغيل السيرفر في خلفية منفصلة
threading.Thread(target=run_server, daemon=True).start()

def main():
    print("🟢 [الدالة الرئيسية] بدأت وحلقة الفحص ستعمل الآن...", flush=True)
    cycle = 1
    
    while True:
        print(f"🔄 [مراقبة حية] الدورة رقم {cycle} تبدأ الآن...", flush=True)
        try:
            # اختبار اتصال بسيط بمنصة Bybit للتأكد من الشبكة
            url = "https://api.bybit.com/v5/market/tickers?category=linear"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ [اتصال ناجح] تم الاتصال بـ Bybit في الدورة {cycle}", flush=True)
            else:
                print(f"⚠️ [تحذير] استجابة Bybit غير مرجوة: {response.status_code}", flush=True)
        except Exception as e:
            print(f"❌ [خطأ في الاتصال] {e}", flush=True)
            
        cycle += 1
        print(f"⏳ الانتظار للدورة القادمة...\n", flush=True)
        time.sleep(10)

if __name__ == "__main__":
    main()
