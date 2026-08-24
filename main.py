import asyncio
import json
import websockets
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- خادم Render يمنع توقف السكربت ---
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

# قائمة أسرع 10 عملات سيولة للتجربة المباشرة
SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "dogeusdt", "pepeusdt", "wifusdt", "nearusdt", "suiusdt"]
TIMEFRAMES = ["5m", "15m"]

async def start_radar():
    streams = []
    for s in SYMBOLS:
        for tf in TIMEFRAMES:
            streams.append(f"{s}@kline_{tf}")
    
    url = f"wss://fstream.binance.com/stream?streams={'/'.join(streams)}"
    
    print("⏳ جاري الاتصال بالسيرفر...", flush=True)

    async with websockets.connect(url) as ws:
        print("✅ تم الاتصال! البيانات ستبدأ بالتدفق فوراً أدناه:\n", flush=True)
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            
            if 'data' in data:
                k = data['data']['k']
                symbol = k['s']
                tf = k['i']
                open_p = float(k['o'])
                close_p = float(k['c'])
                
                # تحديث مستمر حي أمامك:
                if close_p < open_p:
                    print(f"🔴 [شمعة حمراء] {symbol:<10} | فريم: {tf:<3} | الافتتاح: {open_p} | الإغلاق: {close_p}", flush=True)
                else:
                    print(f"🟢 [شمعة خضراء] {symbol:<10} | فريم: {tf:<3} | الافتتاح: {open_p} | الإغلاق: {close_p}", flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(start_radar())
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}", flush=True)
