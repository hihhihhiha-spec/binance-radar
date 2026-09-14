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

# --- 2. إعدادات بينانس ---
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

# --- دالة لجلب أعلى العملات حسب نسبة التغير المئوي لآخر 24 ساعة في الفيوتشرز ---
def get_top_gainers_futures(limit=200):
    try:
        print("⏳ جاري تحميل الأسواق من بينانس...", flush=True)
        exchange.load_markets()
        print("⏳ جاري جلب أسعار التغير (Tickers)...", flush=True)
        tickers = exchange.fetch_tickers()
        valid_symbols = []
        
        for symbol, ticker in tickers.items():
            if symbol.endswith('/USDT:USDT') or (symbol.endswith('/USDT') and exchange.market(symbol).get('swap', False)):
                percentage = ticker.get('percentage', 0)
                if percentage is None:
                    percentage = -999999
                clean_symbol = symbol.split(':')[0]
                valid_symbols.append((clean_symbol, float(percentage)))
        
        valid_symbols.sort(key=lambda x: x[1], reverse=True)
        top_symbols = [item[0] for item in valid_symbols[:limit]]
        print(f"✅ تم جلب أعلى {len(top_symbols)} عملة بنجاح.", flush=True)
        return top_symbols
    except Exception as e:
        print(f"❌ Error fetching top gainers symbols: {e}", flush=True)
        return []

TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '4h']

sent_alerts = {}

# --- الاستراتيجية الأولى (بدون أي تعديل) ---
def check_logic(symbol, tf):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=6)
        if len(bars) < 5: 
            return False
        
        for i in range(len(bars) - 4):
            c1, c2, c3, c4, c5 = bars[i], bars[i+1], bars[i+2], bars[i+3], bars[i+4]
            
            # --- تفكيك الشمعة 1 ---
            o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
            is_red_1 = cl1 < o1
            body1 = abs(o1 - cl1)
            lower_wick1 = min(o1, cl1) - l1

            # --- تفكيك الشمعة 2 ---
            o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]
            is_red_2 = cl2 < o2
            body2 = abs(o2 - cl2)
            lower_wick2 = min(o2, cl2) - l2
            range2 = h2 - l2
            
            is_full_red_2 = is_red_2 and (body2 > range2 * 0.45)
            cond_reds = is_red_1 and is_full_red_2 and (body2 > body1) and (lower_wick2 > lower_wick1)

            # --- تفكيك الشمعة 3 ---
            o3, h3, l3, cl3 = c3[1], c3[2], c3[3], c3[4]
            is_green_3 = cl3 > o3
            body3 = abs(o3 - cl3)
            range3 = h3 - l3
            
            is_full_green_3 = is_green_3 and (body3 > range3 * 0.4)
            body2_top = max(o2, cl2)
            body2_bottom = min(o2, cl2)
            
            is_c3_inside_body2 = (h3 <= body2_top) and (l3 >= body2_bottom)
            body2_middle = (body2_top + body2_bottom) / 2
            is_c3_close_in_middle = abs(cl3 - body2_middle) <= (body2 * 0.25)

            # --- تفكيك الشمعة 4 ---
            o4, h4, l4, cl4 = c4[1], c4[2], c4[3], c4[4]
            is_green_4 = cl4 > o4
            is_c4_break = is_green_4 and (cl4 > h3)

            # --- تفكيك الشمعة 5 ---
            o5, h5, l5, cl5 = c5[1], c5[2], c5[3], c5[4]
            is_red_5 = cl5 < o5
            body5 = abs(o5 - cl5)
            range5 = h5 - l5
            
            body4_top = max(o4, cl4)
            body4_bottom = min(o4, cl4)
            
            is_full_red_5 = is_red_5 and (body5 > range5 * 0.4)
            is_c5_inside_body4 = (h5 <= body4_top) and (l5 >= body4_bottom)
            
            body4_middle = (body4_top + body4_bottom) / 2
            is_c5_close_in_middle = abs(cl5 - body4_middle) <= (abs(o4 - cl4) * 0.25)
            
            upper_wick_4 = h4 - max(o4, cl4)
            upper_wick_5 = h5 - max(o5, cl5)
            is_upper_wick_smaller = upper_wick_5 < upper_wick_4

            if (cond_reds and 
                is_full_green_3 and is_c3_inside_body2 and is_c3_close_in_middle and 
                is_c4_break and 
                is_full_red_5 and is_c5_inside_body4 and is_c5_close_in_middle and is_upper_wick_smaller):
                
                candle_timestamp = c5[0]
                alert_key = f"{symbol}_{tf}_{candle_timestamp}_s1"
                
                if alert_key not in sent_alerts:
                    sent_alerts[alert_key] = True
                    return True
                
        return False
    except Exception as e:
        return False


# --- الاستراتيجية الثانية (معدلة ومشددة بالكامل) ---
def check_strategy_2(symbol, tf):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
        if len(bars) < 4: 
            return False
        
        for i in range(len(bars) - 3):
            c1, c2, c3, c4 = bars[i], bars[i+1], bars[i+2], bars[i+3]
            
            # الشمعة 1: حمراء وممتلئة جداً (أكثر من 50% من طولها جسم)
            o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
            is_red_1 = cl1 < o1
            body1 = abs(o1 - cl1)
            range1 = h1 - l1
            is_full_1 = is_red_1 and (range1 > 0 and body1 > range1 * 0.5)
            lower_wick1 = min(o1, cl1) - l1

            # الشمعة 2: حمراء ممتلئة، حجمها أصغر من 1، وديلها السفلي أصغر من 1
            o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]
            is_red_2 = cl2 < o2
            body2 = abs(o2 - cl2)
            range2 = h2 - l2
            is_full_2 = is_red_2 and (range2 > 0 and body2 > range2 * 0.5)
            lower_wick2 = min(o2, cl2) - l2
            
            cond_c2 = is_full_2 and (body2 < body1) and (lower_wick2 < lower_wick1)

            # الشمعة 3: خضراء ممتلئة، تكسر أعلى شمعة 2، وديلها السفلي لا يتعدى قاع شمعة 2
            o3, h3, l3, cl3 = c3[1], c3[2], c3[3], c3[4]
            is_green_3 = cl3 > o3
            body3 = abs(o3 - cl3)
            range3 = h3 - l3
            is_full_3 = is_green_3 and (range3 > 0 and body3 > range3 * 0.5)
            is_break_3 = cl3 > h2  # إغلاق صريح فوق قمة شمعة 2
            is_wick_c3_valid = l3 >= l2  # الديل السفلي للخضراء لا ينزل تحت قاع الحمراء الثانية

            # الشمعة 4: حمراء داخل الشمعة الخضراء، وإغلاق فوق نصف الشمعة الخضراء
            o4, h4, l4, cl4 = c4[1], c4[2], c4[3], c4[4]
            is_red_4 = cl4 < o4
            is_inside_c3 = (h4 <= h3 and l4 >= l3)
            green_middle_3 = (o3 + cl3) / 2
            is_close_above_middle_3 = cl4 > green_middle_3

            if (is_full_1 and cond_c2 and 
                is_full_3 and is_break_3 and is_wick_c3_valid and 
                is_red_4 and is_inside_c3 and is_close_above_middle_3):
                
                candle_timestamp = c4[0]
                alert_key = f"{symbol}_{tf}_{candle_timestamp}_s2"
                
                if alert_key not in sent_alerts:
                    sent_alerts[alert_key] = True
                    return True

        return False
    except Exception as e:
        return False


print("🚀 Radar Started with Top 200 Gainers & 2 Strategies.", flush=True)
send_telegram_message("🚀 تم تشغيل الرادار (أعلى 200 عملة حسب التغير المئوي 24 ساعة) بنجاح.")

while True:
    try:
        print("⏳ جاري استدعاء get_top_gainers_futures()...", flush=True)
        active_symbols = get_top_gainers_futures(limit=200)
        
        if not active_symbols:
            print("⚠️ لم يتم العثور على أي عملات، سيتم الانتظار 15 ثانية وإعادة المحاولة...", flush=True)
            time.sleep(15)
            continue

        print(f"📋 Loaded {len(active_symbols)} symbols. Starting loop...", flush=True)

        for index, symbol in enumerate(active_symbols, 1):
            for tf in TIMEFRAMES:
                print(f"🔍 [فتح وفحص] العملة رقم {index}/{len(active_symbols)}: {symbol} | الفريم: {tf}", flush=True)
                
                # فحص الاستراتيجية الأولى
                if check_logic(symbol, tf):
                    alert_msg = f"🎯 *تنبيه رادار بينانس (استراتيجية 1)*\n\n🔹 العملة: `{symbol}`\n⏱️ الفريم: `{tf}`\n⏰ الوقت: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                    print(f"ALERT FOUND (Strategy 1): {symbol} | {tf}", flush=True)
                    send_telegram_message(alert_msg)

                # فحص الاستراتيجية الثانية
                if check_strategy_2(symbol, tf):
                    alert_msg = f"🔥 *تنبيه رادار بينانس (استراتيجية 2)*\n\n🔹 العملة: `{symbol}`\n⏱️ الفريم: `{tf}`\n⏰ الوقت: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                    print(f"ALERT FOUND (Strategy 2): {symbol} | {tf}", flush=True)
                    send_telegram_message(alert_msg)
                
                time.sleep(0.4)
        
        print("--- Cycle Finished. Refreshing Top Gainers & Restarting ---", flush=True)
        time.sleep(15)
    except Exception as e:
        print(f"❌ Main Loop Error: {e}", flush=True)
        time.sleep(30)
