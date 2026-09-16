import sys
import ccxt
import time
import os
import threading
import requests
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

# --- 1. حل مشكلة توقف Render ---
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

# --- 2. إعدادات بايبيت فيوتشرز (Bybit USDT Linear Perpetual) ---
exchange = ccxt.bybit({
    'options': {
        'defaultType': 'linear',
    },
    'enableRateLimit': True
})

TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '4h']
sent_alerts = {}

# --- دالة لجلب أعلى العملات صعوداً في فيوتشرز بايبيت ديناميكياً ---
def get_top_futures_gainers(limit=150):
    try:
        print("📡 جاري جلب تيكرات فيوتشرز بايبيت (Bybit Linear)...", flush=True)
        tickers = exchange.fetch_tickers()
        
        movers = []
        seen_symbols = set()
        
        for raw_symbol, data in tickers.items():
            symbol = raw_symbol.split(':')[0]
            if symbol.endswith('/USDT') and symbol not in seen_symbols:
                pct = data.get('percentage')
                if pct is not None:
                    seen_symbols.add(symbol)
                    movers.append((symbol, float(pct)))
        
        if not movers:
            print("⚠️ لم يتم استرجاع أي بيانات للفيوتشرز من بايبيت.", flush=True)
            return []

        movers.sort(key=lambda x: x[1], reverse=True)
        top_symbols = [m[0] for m in movers[:limit]]
        print(f"🔥 تم جلب أعلى {len(top_symbols)} عملات في فيوتشرز بايبيت بنجاح.", flush=True)
        return top_symbols
        
    except Exception as e:
        print(f"❌ خطأ أثناء جلب فيوتشرز بايبيت: {e}", flush=True)
        return []

# --- الاستراتيجية الرابعة الصارمة فقط ---
def check_strict_strategy_4(symbol, tf):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
        if len(bars) < 4: 
            return False
        
        for i in range(len(bars) - 3):
            c1, c2, c3, c4 = bars[i], bars[i+1], bars[i+2], bars[i+3]
            
            # 1. الشمعة الأولى: حمراء صارمة (الجسم أكبر بوضوح من الذيول)
            o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
            is_red_1 = cl1 < o1
            body1 = abs(o1 - cl1)
            upper_wick1 = h1 - max(o1, cl1)
            lower_wick1 = min(o1, cl1) - l1
            is_body_strict_1 = is_red_1 and (body1 > upper_wick1 * 1.5) and (body1 > lower_wick1 * 1.5)
            
            # 2. الشمعة الثانية: حمراء، تكسر الأولى، أصغر منها حجماً
            o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]
            is_red_2 = cl2 < o2
            body2 = abs(o2 - cl2)
            is_smaller_red_2 = is_red_2 and (body2 < body1) and (l2 < l1)
            
            # 3. الشمعة الثالثة: خضراء، ذيلها السفلي لا يكسر تحت الثانية، تكسر الثانية صعوداً، وتغلق في منتصف الأولى
            o3, h3, l3, cl3 = c3[1], c3[2], c3[3], c3[4]
            is_green_3 = cl3 > o3
            is_wick_safe_3 = l3 >= l2
            is_break_3 = cl3 > h2
            
            middle_c1 = (o1 + cl1) / 2
            is_close_in_middle_1 = abs(cl3 - middle_c1) <= (body1 * 0.2)
            
            # 4. الشمعة الرابعة: تغلق فوق نصف الشمعة الخضراء الثالثة بصرامة
            o4, h4, l4, cl4 = c4[1], c4[2], c4[3], c4[4]
            body3 = abs(o3 - cl3)
            middle_c3 = (o3 + cl3) / 2
            is_close_above_middle_3 = cl4 > middle_c3

            if (is_body_strict_1 and 
                is_smaller_red_2 and 
                is_green_3 and is_wick_safe_3 and is_break_3 and is_close_in_middle_1 and 
                is_close_above_middle_3):
                
                candle_timestamp = c4[0]
                alert_key = f"{symbol}_{tf}_{candle_timestamp}_strict_s4"
                
                if alert_key not in sent_alerts:
                    sent_alerts[alert_key] = True
                    return True

        return False
    except Exception:
        return False


print("🚀 Radar Started with Strict Strategy 4 Only for Bybit Futures.", flush=True)
send_telegram_message("🚀 تم تحديث الرادار: العمل الآن بالاستراتيجية الرابعة الصارمة فقط.")

last_movers_update = 0
top_symbols_cache = []
UPDATE_INTERVAL = 10 * 60  # تحديث القائمة كل 10 دقائق

while True:
    try:
        current_time = time.time()
        if (current_time - last_movers_update) > UPDATE_INTERVAL or not top_symbols_cache:
            top_symbols_cache = get_top_futures_gainers(limit=150)
            last_movers_update = current_time

        if not top_symbols_cache:
            print("⏳ القائمة فارغة حالياً، إعادة المحاولة بعد 15 ثانية...", flush=True)
            time.sleep(15)
            continue

        print(f"📋 بدء فحص {len(top_symbols_cache)} عملة من فيوتشرز بايبيت...", flush=True)

        for index, symbol in enumerate(top_symbols_cache, 1):
            for tf in TIMEFRAMES:
                print(f"🔍 [فحص] ({index}/{len(top_symbols_cache)}) العملة: {symbol} | الفريم: {tf}", flush=True)
                
                if check_strict_strategy_4(symbol, tf):
                    alert_msg = f"💎 *تنبيه بايبيت (الاستراتيجية الرابعة الصارمة)*\n\n🔹 العملة: `{symbol}`\n⏱️ الفريم: `{tf}`\n⏰ الوقت: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                    send_telegram_message(alert_msg)
                
                time.sleep(0.4)
        
        print("--- اكتملت دورة الفحص. انتظار قليل ---", flush=True)
        time.sleep(10)

    except Exception as e:
        print(f"❌ Main Loop Error: {e}", flush=True)
        time.sleep(20)
