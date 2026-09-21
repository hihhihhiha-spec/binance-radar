import sys
import json
import time
import os
import threading
import requests
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- تفعيل الطباعة الفورية بدون تخزين مؤقت ---
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# --- إعدادات تيليجرام ---
TELEGRAM_TOKEN = "8866274181:AAEU7Ofsem4EW87PNo1Uk_sNs0VSejcSmvI"
CHAT_ID = "6141474899"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=5)
        print(f"📤 [تيليجرام] تم الإرسال بنجاح (الكود: {response.status_code})", flush=True)
    except Exception as e:
        print(f"❌ Telegram Error: {e}", flush=True)

# --- سيرفر HTTP أساسي لـ Render (يعمل فوراً لمنع تعليق In progress) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bybit Radar is Running Successfully")
    def log_message(self, format, *args):
        pass

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"🌐 [سيرفر Render] يعمل بنجاح على البورت {port}", flush=True)
        sys.stdout.flush()
        server.serve_forever()
    except Exception as e:
        print(f"❌ خطأ في تشغيل السيرفر: {e}", flush=True)
        sys.stdout.flush()

# تشغيل سيرفر الويب في خلفية مستقلة لضمان استجابة Render فوراً
threading.Thread(target=run_http_server, daemon=True).start()

sent_alerts = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def get_top_futures_symbols(limit=100):
    try:
        print("📡 [بايبت] جاري جلب قائمة العملات الصاعدة (Linear Futures)...", flush=True)
        sys.stdout.flush()
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠️ خطأ في الاستجابة (الكود: {response.status_code})", flush=True)
            return []
            
        result = response.json()
        if result.get("retCode") != 0:
            print(f"⚠️ خطأ من API بايبت: {result.get('retMsg')}", flush=True)
            return []
            
        data = result.get("result", {}).get("list", [])
        if not isinstance(data, list):
            return []
        
        movers = []
        for item in data:
            symbol = item.get('symbol', '')
            if symbol.endswith('USDT'):
                try:
                    pct = float(item.get('price24hPcnt', 0)) * 100
                    movers.append((symbol.lower(), pct))
                except ValueError:
                    continue
        
        movers.sort(key=lambda x: x[1], reverse=True)
        
        seen = set()
        top_symbols = []
        for m in movers:
            if m[0] not in seen:
                seen.add(m[0])
                top_symbols.append(m[0])
            if len(top_symbols) >= limit:
                break
                
        print(f"🔥 [نجاح] تم اختيار أعلى {len(top_symbols)} عملة من بايبت.", flush=True)
        sys.stdout.flush()
        return top_symbols
    except Exception as e:
        print(f"❌ خطأ في جلب العملات من بايبت: {e}", flush=True)
        return []

BYBIT_INTERVALS = {
    '15m': '15',
    '30m': '30',
    '1h': '60',
    '4h': '240'
}

def get_klines(symbol, interval, limit=15):
    try:
        bybit_tf = BYBIT_INTERVALS.get(interval, '60')
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol.upper()}&interval={bybit_tf}&limit={limit}"
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("retCode") == 0:
                raw_data = res_json.get("result", {}).get("list", [])
                if isinstance(raw_data, list):
                    candles = []
                    for item in reversed(raw_data):
                        candles.append({
                            'time': int(item[0]),
                            'o': float(item[1]),
                            'h': float(item[2]),
                            'l': float(item[3]),
                            'c': float(item[4])
                        })
                    return candles
    except Exception as e:
        pass
    return []

def evaluate_strategies(symbol, tf, candles):
    try:
        if len(candles) < 7:
            return
        
        c_prev2, c_prev1, c1, c2, c3, c4 = candles[-6], candles[-5], candles[-4], candles[-3], candles[-2], candles[-1]
        
        o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
        o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
        o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']
        o4, h4, l4, cl4 = c4['o'], c4['h'], c4['l'], c4['c']

        def get_wick_body(o, h, l, c):
            body = abs(o - c)
            upper_wick = h - max(o, c)
            lower_wick = min(o, c) - l
            return body, upper_wick, lower_wick

        # --- 1. الاستراتيجية الأولى ---
        strat1_active = False
        try:
            if (c_prev2['h'] >= c_prev1['h'] and c_prev1['h'] >= h1):
                if cl1 < o1:
                    body1, upper_wick1, lower_wick1 = get_wick_body(o1, h1, l1, cl1)
                    if (upper_wick1 > 0 and lower_wick1 > 0 and 
                        body1 > upper_wick1 and body1 > lower_wick1 and 
                        lower_wick1 > upper_wick1):
                        if cl2 < o2:
                            body2, _, _ = get_wick_body(o2, h2, l2, cl2)
                            if body2 < body1 and l2 < l1 and cl2 < l1:
                                if cl3 > o3 and l3 >= l2:
                                    middle_c1 = (h1 + l1) / 2
                                    if middle_c1 <= cl3 <= h1 and h3 <= h1:
                                        middle_c3 = (h3 + l3) / 2
                                        if cl4 > middle_c3:
                                            strat1_active = True
        except Exception:
            pass

        # --- 2. الاستراتيجية الثانية ---
        strat2_active = False
        try:
            if cl1 < o1:
                body1, u_wick1, l_wick1 = get_wick_body(o1, h1, l1, cl1)
                if (u_wick1 > 0 and l_wick1 > 0 and 
                    body1 > u_wick1 and body1 > l_wick1 and 
                    l_wick1 > u_wick1):
                    if cl2 < o2:
                        body2, _, _ = get_wick_body(o2, h2, l2, cl2)
                        if body2 > body1 and l2 < l1:
                            if cl3 > o3:
                                middle_c3 = (h3 + l3) / 2
                                if (l3 >= l1 and h3 <= h1) and (l4 >= l1 and h4 <= h1) and (cl4 > middle_c3):
                                    strat2_active = True
        except Exception:
            pass

        # --- 3. الاستراتيجية الثالثة ---
        strat3_active = False
        try:
            if cl1 < o1:
                body1, u_wick1, l_wick1 = get_wick_body(o1, h1, l1, cl1)
                if body1 > l_wick1 and l_wick1 > u_wick1:
                    if cl2 < o2:
                        body2, u_wick2, l_wick2 = get_wick_body(o2, h2, l2, cl2)
                        if l2 < l1 and cl2 < (l1 - l_wick1) and l_wick2 > 0:
                            if cl3 > o3:
                                if (l3 >= l1 and h3 <= h1) and (l3 >= l2 and cl3 > h2):
                                    strat3_active = True
        except Exception:
            pass

        # --- إرسال التنبيهات ---
        if strat1_active:
            alert_key_1 = f"{symbol}_{tf}_{c4['time']}_strat1"
            if alert_key_1 not in sent_alerts:
                sent_alerts[alert_key_1] = True
                send_telegram_message(f"💎 *تنبيه بايبت (الاستراتيجية الأولى)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`")

        if strat2_active:
            alert_key_2 = f"{symbol}_{tf}_{c4['time']}_strat2"
            if alert_key_2 not in sent_alerts:
                sent_alerts[alert_key_2] = True
                send_telegram_message(f"🚀 *تنبيه بايبت (الاستراتيجية الثانية)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`")

        if strat3_active:
            alert_key_3 = f"{symbol}_{tf}_{c3['time']}_strat3"
            if alert_key_3 not in sent_alerts:
                sent_alerts[alert_key_3] = True
                send_telegram_message(f"⭐ *تنبيه بايبت (الاستراتيجية الثالثة)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`")

    except Exception:
        pass

def main_loop():
    print("🚀 [بدء التشغيل] الرادار يعمل الآن ويراقب السوق...", flush=True)
    sys.stdout.flush()
    send_telegram_message("🟢 تم تشغيل رادار بايبت بنجاح وتجاوز حالة الانتظار.")

    # تقليص الفريمات والعملات قليلاً لضمان سرعة الدورة وعدم تعليق السيرفر
    timeframes = ['15m', '30m', '1h', '4h']
    symbols = []
    last_update_time = datetime.min

    while True:
        try:
            current_time = datetime.now()
            
            if not symbols or (current_time - last_update_time >= timedelta(hours=3)):
                symbols = get_top_futures_symbols(limit=100)
                last_update_time = current_time
                if not symbols:
                    time.sleep(30)
                    continue

            print(f"🔄 جاري فحص {len(symbols)} عملة...", flush=True)
            sys.stdout.flush()
            
            for symbol in symbols:
                for tf in timeframes:
                    candles = get_klines(symbol, tf, limit=15)
                    if candles:
                        evaluate_strategies(symbol, tf, candles)
                    time.sleep(0.05)
                    
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ خطأ في الدورة الرئيسية: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main_loop()
