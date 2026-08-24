import asyncio
import json
import websockets
import os
import sys
import threading
import requests
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

# --- 2. جلب أعلى 50 عملة سيولة (طلب واحد فقط مرة كل دورة) ---
def get_top_symbols(limit=50):
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        res = requests.get(url, timeout=10).json()
        usdt_pairs = [
            item for item in res 
            if item['symbol'].endswith('USDT')
        ]
        usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        symbols = [item['symbol'].lower() for item in usdt_pairs[:limit]]
        print(f"✅ تم اختيار أعلى {len(symbols)} عملة سيولة.", flush=True)
        return symbols
    except Exception as e:
        print(f"⚠️ يتعذر جلب قائمة السيولة (قد تكون ما زلت محظوراً مؤقتاً): {e}", flush=True)
        return []

# سجل منع التكرار
alerted_candles = set()

# --- 3. الاستماع البث الحي عبر WebSockets ---
async def binance_websocket_radar():
    symbols = get_top_symbols(limit=50)
    if not symbols:
        print("⏳ انتظار دقيقتين لفك حظر الـ IP من باينانس...", flush=True)
        await asyncio.sleep(120)
        return

    # بناء رابط البث المباشر للشمعات (5m و 15m)
    streams = []
    for s in symbols:
        streams.append(f"{s}@kline_5m")
        streams.append(f"{s}@kline_15m")
    
    stream_url = f"wss://fstream.binance.com/stream?streams={'/'.join(streams)}"
    
    print("🚀 اتصال بـ WebSocket الخاص ببينانس... لا يوجد طلبات HTTP تسبب حظر!", flush=True)

    async for websocket in websockets.connect(stream_url):
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                if 'data' in data:
                    kline = data['data']['k']
                    symbol = kline['s']
                    tf = kline['i']
                    open_price = float(kline['o'])
                    close_price = float(kline['c'])
                    kline_time = kline['t']

                    # فحص الشمعة الحمراء الحية
                    if close_price < open_price:
                        alert_id = f"{symbol}_{tf}_{kline_time}"
                        if alert_id not in alerted_candles:
                            alerted_candles.add(alert_id)
                            print(f"\n🔥 [تنبيه WebSocket حي] {symbol} | شمعة حمراء! | الفريم: {tf} | السعر: {close_price} | الوقت: {datetime.now().strftime('%H:%M:%S')}\n", flush=True)
                            play_radar_sound()

                    # تنظيف السجل
                    if len(alerted_candles) > 1000:
                        alerted_candles.clear()

        except websockets.ConnectionClosed:
            print("⚠️ انقطع الاتصال، إعادة الاتصال تلقائياً...", flush=True)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"خطأ في الـ WebSocket: {e}", flush=True)
            await asyncio.sleep(5)

# --- 4. تشغيل المحرك الرئيسي ---
if __name__ == "__main__":
    while True:
        try:
            asyncio.run(binance_websocket_radar())
        except Exception as e:
            print(f"إعادة تشغيل النظام: {e}", flush=True)
            time.sleep(10)
