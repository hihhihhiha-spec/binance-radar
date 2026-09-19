import sys
import json
import time
import os
import threading
import requests
import websocket
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- إعدادات تيليجرام ---
TELEGRAM_TOKEN = "8866274181:AAEU7Ofsem4EW87PNo1Uk_sNs0VSejcSmvI"
CHAT_ID = "6141474899"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=5)
        print(f"📤 [تيليجرام] حالة الإرسال: {response.status_code}", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ Telegram Send Error: {e}", flush=True)
        sys.stdout.flush()

# --- سيرفر HTTP لضمان استمرار عمل Render ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar is Active")
    def log_message(self, format, *args): 
        pass

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🌐 HTTP Server running on port {port}", flush=True)
    sys.stdout.flush()
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

market_data = {}
sent_alerts = {}

def get_top_binance_symbols(limit=30):
    try:
        print("📡 جاري جلب قائمة العملات من بينانس...", flush=True)
        sys.stdout.flush()
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        movers = []
        for item in data:
            symbol = item['symbol']
            if symbol.endswith('USDT'):
                pct = float(item['priceChangePercent'])
                movers.append((symbol.lower(), pct))
        
        movers.sort(key=lambda x: x[1], reverse=True)
        top_symbols = [m[0] for m in movers[:limit]]
        print(f"🔥 تم اختيار أعلى {len(top_symbols)} عملة للمراقبة المباشرة.", flush=True)
        sys.stdout.flush()
        return top_symbols
    except Exception as e:
        print(f"❌ خطأ في جلب العملات: {e}", flush=True)
        sys.stdout.flush()
        return []

def evaluate_strategy(symbol, tf, candles):
    try:
        if len(candles) < 7:
            return
        
        c_prev2, c_prev1, c1, c2, c3, c4 = candles[-6], candles[-5], candles[-4], candles[-3], candles[-2], candles[-1]
        
        o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
        o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
        o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']
        o4, h4, l4, cl4 = c4['o'], c4['h'], c4['l'], c4['c']
        
        if not (c_prev2['h'] >= c_prev1['h'] and c_prev1['h'] >= h1):
            return

        if cl1 >= o1: return
        body1 = abs(o1 - cl1)
        upper_wick1 = h1 - max(o1, cl1)
        lower_wick1 = min(o1, cl1) - l1
        if not (body1 > upper_wick1 and body1 > lower_wick1): return
        if upper_wick1 > lower_wick1: return

        if cl2 >= o2: return
        body2 = abs(o2 - cl2)
        if not (body2 < body1 and l2 < l1 and cl2 < l1): return

        if cl3 <= o3: return
        if l3 < l2: return 
        
        middle_c1 = (h1 + l1) / 2
        if cl3 < middle_c1: return
        if cl3 > h1: return
        if h3 > h1: return

        middle_c3 = (h3 + l3) / 2
        if cl4 <= middle_c3: return

        alert_key = f"{symbol}_{tf}_{c4['time']}"
        if alert_key not in sent_alerts:
            sent_alerts[alert_key] = True
            msg = f"💎 *تنبيه بينانس*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
            send_telegram_message(msg)
            print(f"🎯 تم إرسال تنبيه مطابقة للعملة: {symbol.upper()}", flush=True)
            sys.stdout.flush()

    except Exception as e:
        print(f"خطأ في الاستراتيجية: {e}", flush=True)
        sys.stdout.flush()

def on_message(ws, message):
    try:
        data = json.loads(message)
        if 'k' in data:
            k = data['k']
            symbol = data['s'].lower()
            tf = k['i']
            is_closed = k['x']
            
            candle = {
                'time': k['t'],
                'o': float(k['o']), 'h': float(k['h']),
                'l': float(k['l']), 'c': float(k['c'])
            }
            
            key = f"{symbol}_{tf}"
            if key not in market_data:
                market_data[key] = []
            
            if market_data[key] and market_data[key][-1]['time'] == candle['time']:
                market_data[key][-1] = candle
            else:
                market_data[key].append(candle)
                if len(market_data[key]) > 20:
                    market_data[key].pop(0)
            
            # طباعة فورية تظهر في السجلات مباشرة
            print(f"🔍 فحص العملة: {symbol.upper()} | الفريم: {tf} | السعر: {candle['c']}", flush=True)
            sys.stdout.flush()
            
            if is_closed:
                print(f"🔒 إغلاق شمعة للعملة: {symbol.upper()} على فريم {tf}", flush=True)
                sys.stdout.flush()
                evaluate_strategy(symbol, tf, market_data[key])
    except Exception as e:
        print(f"خطأ في رسالة WS: {e}", flush=True)
        sys.stdout.flush()

def on_error(ws, error):
    print(f"WS Error: {error}", flush=True)
    sys.stdout.flush()

def on_close(ws, code, msg):
    print("WS Closed. Reconnecting...", flush=True)
    sys.stdout.flush()
    time.sleep(3)
    start_websocket_radar()

def on_open(ws):
    print("✅ تم الاتصال بنجاح بقنوات بينانس الحية!", flush=True)
    sys.stdout.flush()
    send_telegram_message("🟢 تم تشغيل رادار بينانس بنجاح وبدأ المراقبة المباشرة.")

def start_websocket_radar():
    symbols = get_top_binance_symbols(limit=30)
    if not symbols:
        time.sleep(5)
        start_websocket_radar()
        return

    timeframes = ['1m', '5m', '1h']
    
    streams = [f"{s}@kline_{tf}" for s in symbols for tf in timeframes]
    stream_url = f"wss://fstream.binance.com/stream?streams={'/'.join(streams)}"
    
    ws = websocket.WebSocketApp(
        stream_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever(ping_interval=30, ping_timeout=10)

if __name__ == "__main__":
    start_websocket_radar()
