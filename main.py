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
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Send Error: {e}", flush=True)

# --- 1. حل مشكلة توقف سيرفر Render ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Binance WS Radar is Active")
    def log_message(self, format, *args): return

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_port_server, daemon=True).start()

# تخزين الشموع الحية لكل عملة وفريم
market_data = {}
sent_alerts = {}

# --- جلب أعلى العملات تداولاً عبر REST لمرة واحدة (آمن تماماً ولا يسبب حظر) ---
def get_top_binance_symbols(limit=100):
    try:
        print("📡 جاري جلب قائمة العملات من بينانس...", flush=True)
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
        print(f"🔥 تم اختيار أعلى {len(top_symbols)} عملة للربط المباشر بنجاح.", flush=True)
        return top_symbols
    except Exception as e:
        print(f"❌ خطأ في جلب العملات: {e}", flush=True)
        return []

# --- التحقق الهندسي الصارم (صفر تسامح + موجة هابطة + تصفية الذيول) ---
def evaluate_strategy(symbol, tf, candles):
    try:
        if len(candles) < 7:
            return
        
        c_prev2, c_prev1, c1, c2, c3, c4 = candles[-6], candles[-5], candles[-4], candles[-3], candles[-2], candles[-1]
        
        o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
        o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
        o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']
        o4, h4, l4, cl4 = c4['o'], c4['h'], c4['l'], c4['c']
        
        # 0. شرط الترند الهابط (موجة هابطة حقيقية قبل النموذج)
        if not (c_prev2['h'] >= c_prev1['h'] and c_prev1['h'] >= h1):
            return

        # 1. الشمعة الأولى: حمراء، جسمها واضح أكبر من الذيول، وذيلها العلوي ليس أكبر من ذيلها السفلي
        if cl1 >= o1: return
        body1 = abs(o1 - cl1)
        upper_wick1 = h1 - max(o1, cl1)
        lower_wick1 = min(o1, cl1) - l1
        if not (body1 > upper_wick1 and body1 > lower_wick1): return
        if upper_wick1 > lower_wick1: return

        # 2. الشمعة الثانية: حمراء، أصغر حجماً، وتخرج تماماً من الأولى من الأسفل وقاعها هو القاع الأدنى المطلق للموجة
        if cl2 >= o2: return
        body2 = abs(o2 - cl2)
        if not (body2 < body1 and l2 < l1 and cl2 < l1): return

        # 3. الشمعة الثالثة (الخضراء):
        if cl3 <= o3: return
        if l3 < l2: return 
        
        # خط أحمر صارم: إغلاق الشمعة الثالثة فوق منتصف الشمعة الأولى حصرياً
        middle_c1 = (h1 + l1) / 2
        if cl3 < middle_c1: return
        if cl3 > h1: return
        if h3 > h1: return

        # 4. الشمعة الرابعة: تغلق فوق منتصف الشمعة الثالثة
        middle_c3 = (h3 + l3) / 2
        if cl4 <= middle_c3: return

        alert_key = f"{symbol}_{tf}_{c4['time']}_ws_strict"
        if alert_key not in sent_alerts:
            sent_alerts[alert_key] = True
            msg = f"💎 *تنبيه بينانس الحي (WebSocket)*\n\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`\n⏰ الوقت: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            send_telegram_message(msg)
            print(f"🎯 تم إرسال تنبيه مطابق: {symbol} على فريم {tf}", flush=True)

    except Exception as e:
        pass

# --- استقبال بيانات الـ WebSocket الحية ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        if 'k' in data:
            k = data['k']
            symbol = data['s'].lower()
            tf = k['i']
            is_closed = k['x'] # هل اغلقة الشمعة؟
            
            candle = {
                'time': k['t'],
                'o': float(k['o']),
                'h': float(k['h']),
                'l': float(k['l']),
                'c': float(k['c'])
            }
            
            key = f"{symbol}_{tf}"
            if key not in market_data:
                market_data[key] = []
            
            # تحديث أو إضافة الشمعة
            if market_data[key] and market_data[key][-1]['time'] == candle['time']:
                market_data[key][-1] = candle
            else:
                market_data[key].append(candle)
                if len(market_data[key]) > 20:
                    market_data[key].pop(0)
            
            # الفحص فقط عند إغلاق الشمعة لضمان الدقة المطلقة
            if is_closed:
                evaluate_strategy(symbol, tf, market_data[key])
    except Exception as e:
        pass

def on_error(ws, error):
    print(f"WS Error: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print("WS Closed. Reconnecting in 5 seconds...", flush=True)
    time.sleep(5)
    start_websocket_radar()

def on_open(ws):
    print("✅ Connected to Binance WebSocket Stream successfully!", flush=True)
    send_telegram_message("🚀 تم تفعيل رادار بينانس الحي عبر WebSocket بنجاح وبدون أي حظر.")

def start_websocket_radar():
    symbols = get_top_binance_symbols(limit=100)
    if not symbols:
        time.sleep(10)
        start_websocket_radar()
        return

    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '4h']
    
    # بناء روابط الاستماع لكل العملات والفريمات دفعة واحدة
    streams = []
    for s in symbols:
        for tf in timeframes:
            streams.append(f"{s}@kline_{tf}")
    
    # بينانس تدعم دمج الـ streams في رابط واحد طويل
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
