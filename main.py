import asyncio
import ccxt.pro as ccxtpro
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- 0. دالة الصوت التنبيهي ---
def play_radar_sound():
    try:
        if sys.platform == "win32":
            import winsound
            for _ in range(3):
                winsound.Beep(2000, 300)
                await asyncio.sleep(0.05)
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

# --- 2. إعدادات WebSocket ---
exchange = ccxtpro.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
})

TIMEFRAMES = ['1m', '5m', '15m']
detected_signals = set()

# --- 3. خوارزمية فحص النمط ---
def is_pattern_valid(c1, c2, c3):
    o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
    o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]
    o3, h3, l3, cl3 = c3[1], c3[2], c3[3], c3[4]

    if not (cl1 < o1 and cl2 < o2):
        return False
    if not (l2 < l1):
        return False

    body2 = o2 - cl2
    upper_wick2 = h2 - o2
    lower_wick2 = cl2 - l2
    if not (body2 > (upper_wick2 + lower_wick2)):
        return False

    is_green3 = cl3 > o3
    is_inside3 = (h3 <= h2) and (l3 >= l2)
    mid_body2 = cl2 + (body2 / 2.0)
    closes_above_mid3 = cl3 >= mid_body2

    return is_green3 and is_inside3 and closes_above_mid3

# --- 4. فحص العملة عبر WebSocket ---
async def watch_symbol_tf(symbol, tf):
    while True:
        try:
            bars = await exchange.watch_ohlcv(symbol, timeframe=tf, limit=4)
            if not bars or len(bars) < 4:
                continue

            c1, c2, c3 = bars[-4], bars[-3], bars[-2]
            candle_time = c3[0]

            if is_pattern_valid(c1, c2, c3):
                signal_key = f"{symbol}_{tf}_{candle_time}"
                if signal_key not in detected_signals:
                    detected_signals.add(signal_key)
                    print(f"\n🎯🎯🎯 [صيد جديد عبر WebSocket] {symbol} | الفريم: {tf} 🎯🎯🎯\n", flush=True)
                    play_radar_sound()
        except Exception as e:
            await asyncio.sleep(5)

async def main():
    print("🔄 جاري تحميل العملات وبدء شبكة WebSockets الخفيفة...", flush=True)
    try:
        markets = await exchange.load_markets()
        symbols = [symbol for symbol, data in markets.items() if symbol.endswith('/USDT') and data.get('active', True)]
        print(f"✅ تم ربط {len(symbols)} عملة بقناة البث الحي المستمر!", flush=True)
    except Exception as e:
        print(f"⚠️ انتظر انتهاء حظر باينانس المؤقت (IP Ban): {e}", flush=True)
        return

    tasks = []
    # اختيار أهم العملات للتركيز على استهلاك البيانات بدون حظر
    for symbol in symbols[:150]:
        for tf in TIMEFRAMES:
            tasks.append(watch_symbol_tf(symbol, tf))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
