import asyncio
import json
import websockets
import os
import sys
import threading
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- 0. دالة الصوت ---
def play_radar_sound():
    try:
        if sys.platform == "win32":
            import winsound
            winsound.Beep(2000, 300)
        else:
            print('\a', flush=True)
    except Exception:
        pass

# --- 1. خادم Render ---
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

# --- 2. جلب قائمة العملات (20 عملة فقط لضمان عمل الرابط) ---
SYMBOLS = [
    "btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", 
    "adausdt", "avaxusdt", "dogeusdt", "linkusdt", "nearusdt",
    "maticusdt", "opusdt", "arbusdt", "shibusdt", "pepeusdt",
    "wifusdt", "bonkusdt", "flokiusdt", "suiusdt", "aptusdt"
]

TIMEFRAMES = ["5m", "15m"]
alerted_candles = set()

# --- 3. تشغيل الـ WebSocket ---
async def start_radar():
    # بناء البث
    streams = []
    for s in SYMBOLS:
        for tf in TIMEFRAMES:
            streams.append(f"{s}@kline_{tf}")
    
    url = f"wss://fstream.binance.com/stream?streams={'/'.join(streams)}"
    
    print("⏳ جاري الاتصال بـ باينانس...", flush=True)

    async with websockets.connect(url) as ws:
        print("✅ تم الاتصال بنجاح! الرادار يعمل الآن ويستقبل البيانات حياً...", flush=True)
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            
            if 'data' in data:
                k = data['data']['k']
                symbol = k['s']
                tf = k['i']
                open_p = float(k['o'])
                close_p = float(k['c'])
                k_time = k['t']

                # طباعة نقطة للتأكد من وصول البيانات
                # إذا كانت الشمعة حمراء
                if close_p < open_p:
                    alert_id = f"{symbol}_{tf}_{k_time}"
                    if alert_id not in alerted_candles:
                        alerted_candles.add(alert_id)
                        print(f"\n🚨 [شمعة حمراء] {symbol} | فريم: {tf} | الإغلاق الحالي: {close_p} | الوقت: {datetime.now().strftime('%H:%M:%S')}\n", flush=True)
                        play_radar_sound()

                if len(alerted_candles) > 500:
                    alerted_candles.clear()

if __name__ == "__main__":
    try:
        asyncio.run(start_radar())
    except Exception as e:
        print(f"❌ حدث خطأ: {e}", flush=True)
