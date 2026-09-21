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
        print(f"📤 [تيليجرام] تم الإرسال (الكود: {response.status_code})", flush=True)
    except Exception as e:
        print(f"❌ Telegram Error: {e}", flush=True)

# --- سيرفر HTTP أساسي لـ Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Multi-Threaded Live Logging Radar is Active")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 [HTTP Server] يعمل على البورت {port}", flush=True)
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

sent_alerts = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Chrome/122.0.0.0 Safari/537.36)",
    "Accept": "application/json"
}

# --- جلب أعلى 500 عملة صاعدة من بايبت ---
def get_top_futures_symbols(limit=500):
    try:
        print("📡 [بايبت] جاري جلب قائمة أعلى العملات (Linear Futures)...", flush=True)
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("retCode") == 0:
                data = result.get("result", {}).get("list", [])
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
                print(f"🔥 [نجاح] تم جلب واعتماد {len(top_symbols)} عملة للفحص.", flush=True)
                return top_symbols
    except Exception as e:
        print(f"❌ خطأ جلب العملات: {e}", flush=True)
    return []

BYBIT_INTERVALS = {
    '1m': '1',
    '3m': '3',
    '5m': '5',
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
    except Exception:
        pass
    return []

def get_wick_body(o, h, l, c):
    body = abs(o - c)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    return body, upper_wick, lower_wick

# --- مهام الاستراتيجيات المستقلة مع طباعة التتبع المباشر ---

def run_strategy_1(symbols, timeframes):
    print("🚀 [تشغيل] محرك الاستراتيجية الأولى بدأ المراقبة...", flush=True)
    while True:
        try:
            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    print(f"🔍 [س1] فحص ({idx+1}/{len(symbols)}): {symbol.upper()} | الفريم: {tf}", flush=True)
                    candles = get_klines(symbol, tf, limit=15)
                    if candles and len(candles) >= 7:
                        c_prev2, c_prev1, c1, c2, c3, c4 = candles[-6], candles[-5], candles[-4], candles[-3], candles[-2], candles[-1]
                        o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
                        o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
                        o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']
                        o4, h4, l4, cl4 = c4['o'], c4['h'], c4['l'], c4['c']

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
                                                        key = f"{symbol}_{tf}_{c4['time']}_s1"
                                                        if key not in sent_alerts:
                                                            sent_alerts[key] = True
                                                            send_telegram_message(f"💎 *تنبيه (الاستراتيجية الأولى)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`")
                                                            print(f"🎯 [س 1 محقق] {symbol.upper()} - {tf}", flush=True)
                    time.sleep(0.02)
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ خطأ في الاستراتيجية الأولى: {e}", flush=True)
            time.sleep(15)

def run_strategy_2(symbols, timeframes):
    print("🚀 [تشغيل] محرك الاستراتيجية الثانية بدأ المراقبة...", flush=True)
    while True:
        try:
            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    print(f"🔍 [س2] فحص ({idx+1}/{len(symbols)}): {symbol.upper()} | الفريم: {tf}", flush=True)
                    candles = get_klines(symbol, tf, limit=15)
                    if candles and len(candles) >= 7:
                        c1, c2, c3, c4 = candles[-4], candles[-3], candles[-2], candles[-1]
                        o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
                        o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
                        o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']
                        o4, h4, l4, cl4 = c4['o'], c4['h'], c4['l'], c4['c']

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
                                                key = f"{symbol}_{tf}_{c4['time']}_s2"
                                                if key not in sent_alerts:
                                                    sent_alerts[key] = True
                                                    send_telegram_message(f"🚀 *تنبيه (الاستراتيجية الثانية)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`")
                                                    print(f"🎯 [س 2 محقق] {symbol.upper()} - {tf}", flush=True)
                    time.sleep(0.02)
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ خطأ في الاستراتيجية الثانية: {e}", flush=True)
            time.sleep(15)

def run_strategy_3(symbols, timeframes):
    print("🚀 [تشغيل] محرك الاستراتيجية الثالثة بدأ المراقبة...", flush=True)
    while True:
        try:
            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    print(f"🔍 [س3] فحص ({idx+1}/{len(symbols)}): {symbol.upper()} | الفريم: {tf}", flush=True)
                    candles = get_klines(symbol, tf, limit=15)
                    if candles and len(candles) >= 7:
                        c1, c2, c3 = candles[-4], candles[-3], candles[-2]
                        o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
                        o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
                        o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']

                        if cl1 < o1:
                            body1, u_wick1, l_wick1 = get_wick_body(o1, h1, l1, cl1)
                            if body1 > l_wick1 and l_wick1 > u_wick1:
                                if cl2 < o2:
                                    _, _, l_wick2 = get_wick_body(o2, h2, l2, cl2)
                                    if l2 < l1 and cl2 < (l1 - l_wick1) and l_wick2 > 0:
                                        if cl3 > o3:
                                            if (l3 >= l1 and h3 <= h1) and (l3 >= l2 and cl3 > h2):
                                                key = f"{symbol}_{tf}_{c3['time']}_s3"
                                                if key not in sent_alerts:
                                                    sent_alerts[key] = True
                                                    send_telegram_message(f"⭐ *تنبيه (الاستراتيجية الثالثة)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`")
                                                    print(f"🎯 [س 3 محقق] {symbol.upper()} - {tf}", flush=True)
                    time.sleep(0.02)
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ خطأ في الاستراتيجية الثالثة: {e}", flush=True)
            time.sleep(15)

def main():
    print("🟢 [البدء الرئيسي] جاري إطلاق الرادار مع طباعة تفاصيل الفحص...", flush=True)
    send_telegram_message("🟢 تم تشغيل الرادار مع تفعيل طباعة العملات قيد الفحص بالسجلات.")

    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '4h']
    
    symbols = get_top_futures_symbols(limit=500)
    if not symbols:
        symbols = ["btcusdt", "ethusdt"]

    def update_symbols_periodically():
        nonlocal symbols
        while True:
            time.sleep(10800)
            new_symbols = get_top_futures_symbols(limit=500)
            if new_symbols:
                symbols = new_symbols

    threading.Thread(target=update_symbols_periodically, daemon=True).start()

    # تشغيل كل استراتيجية في مسار مستقل مع طباعة تتبع العملات
    threading.Thread(target=run_strategy_1, args=(symbols, timeframes), daemon=True).start()
    threading.Thread(target=run_strategy_2, args=(symbols, timeframes), daemon=True).start()
    threading.Thread(target=run_strategy_3, args=(symbols, timeframes), daemon=True).start()

    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
