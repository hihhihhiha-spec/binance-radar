import sys
import json
import time
import os
import threading
import requests
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- تفعيل الطباعة الفورية ---
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

TELEGRAM_TOKEN = "8866274181:AAEU7Ofsem4EW87PNo1Uk_sNs0VSejcSmvI"
CHAT_ID = "6141474899"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Telegram Error: {e}", flush=True)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Multi-Strategy Crypto Radar (500 Coins) is Active")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

sent_alerts = {}
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_top_futures_symbols(limit=500):
    try:
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json().get("result", {}).get("list", [])
            movers = []
            for item in data:
                symbol = item.get('symbol', '')
                if symbol.endswith('USDT'):
                    try:
                        pct = float(item.get('price24hPcnt', 0)) * 100
                        movers.append((symbol.lower(), pct))
                    except:
                        continue
            movers.sort(key=lambda x: x[1], reverse=True)
            top_symbols = [m[0] for m in movers[:limit]]
            print(f"🔥 [نجاح] تم جلب واعتماد {len(top_symbols)} عملة للفحص.", flush=True)
            return top_symbols
    except Exception as e:
        print(f"❌ خطأ جلب العملات: {e}", flush=True)
    return []

BYBIT_INTERVALS = {'1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30', '1h': '60', '4h': '240'}

def get_klines(symbol, interval, limit=10):
    try:
        bybit_tf = BYBIT_INTERVALS.get(interval, '60')
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol.upper()}&interval={bybit_tf}&limit={limit}"
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("retCode") == 0:
                raw_data = res_json.get("result", {}).get("list", [])
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
    except:
        pass
    return []

def get_wick_body(o, h, l, c):
    body = abs(o - c)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    return body, upper_wick, lower_wick

# دالة الاستراتيجية الجديدة التي أرسلتها
def check_custom_bullish_engulfing(open_p, high_p, low_p, close_p):
    is_red_1 = close_p[2] < open_p[2]
    body_1 = open_p[2] - close_p[2]
    lower_wick_1 = close_p[2] - low_p[2]
    upper_wick_1 = high_p[2] - open_p[2]
    range_1 = high_p[2] - low_p[2]
    
    if range_1 == 0 or body_1 == 0:
        return False

    has_long_lower_wick = lower_wick_1 >= (1.2 * body_1)
    has_small_upper_wick = upper_wick_1 <= (0.3 * body_1)
    cond_candle_1 = is_red_1 and has_long_lower_wick and has_small_upper_wick

    is_green_2 = close_p[1] > open_p[1]
    body_2 = close_p[1] - open_p[1]
    is_engulfing_body = body_2 >= (1.3 * body_1)
    closed_above_red_open = close_p[1] >= open_p[2]
    cond_candle_2 = is_green_2 and is_engulfing_body and closed_above_red_open

    return cond_candle_1 and cond_candle_2

def main():
    print("🟢 [رادار الاستراتيجيتين المتقدم - 500 عملة] بدأ العمل...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار المزدوج (الاستراتيجية الأولى + الاستراتيجية الجديدة) لـ 500 عملة.")

    timeframes = ['1m', '5m', '15m', '1h', '4h']
    symbols = []
    last_update_time = datetime.min
    cycle = 1

    while True:
        try:
            current_time = datetime.now()
            if not symbols or (current_time - last_update_time >= timedelta(hours=3)):
                symbols = get_top_futures_symbols(limit=500)
                last_update_time = current_time
                if not symbols:
                    time.sleep(30)
                    continue

            print(f"\n🔄 [دورة رقم {cycle}] فحص {len(symbols)} عملة للاستراتيجيتين...", flush=True)

            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    candles = get_klines(symbol, tf, limit=10)
                    if not candles or len(candles) < 4:
                        continue
                    
                    # تجهيز مصفوفات الأسعار للاستراتيجية الجديدة
                    # الفهرس [2] هو الشمعة السابقة، والفهرس [1] هو الشمعة الحالية/التالية
                    open_p = [0, candles[-3]['o'], candles[-4]['o']]
                    high_p = [0, candles[-3]['h'], candles[-4]['h']]
                    low_p = [0, candles[-3]['l'], candles[-4]['l']]
                    close_p = [0, candles[-3]['c'], candles[-4]['c']]

                    c1, c2, c3 = candles[-4], candles[-3], candles[-2]
                    o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
                    o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
                    o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']

                    body1, u_wick1, l_wick1 = get_wick_body(o1, h1, l1, cl1)
                    body2, u_wick2, l_wick2 = get_wick_body(o2, h2, l2, cl2)

                    # -------------------------------------------------------------
                    # 1. فحص الاستراتيجية الأولى (Strategy 3 المرنة)
                    # -------------------------------------------------------------
                    max_c1_u_wick = body1 * 0.10
                    max_c2_u_wick = body2 * 0.05
                    
                    is_strategy_1_valid = (
                        cl1 < o1 and u_wick1 <= max_c1_u_wick and
                        cl2 < o2 and u_wick2 <= max_c2_u_wick and
                        cl3 > o3 and (l3 >= l1 and h3 <= h1) and (l3 >= l2 and cl3 > h2)
                    )

                    if is_strategy_1_valid:
                        key1 = f"{symbol}_{tf}_{c3['time']}_strat1"
                        if key1 not in sent_alerts:
                            sent_alerts[key1] = True
                            msg = f"⭐ *تنبيه (الاستراتيجية الأولى)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg)
                            print(f"🚨 [إشارة الاستراتيجية 1] تم إرسال تنبيه لـ {symbol.upper()} - {tf}", flush=True)

                    # -------------------------------------------------------------
                    # 2. فحص الاستراتيجية الجديدة (Custom Bullish Engulfing)
                    # -------------------------------------------------------------
                    is_strategy_new_valid = check_custom_bullish_engulfing(open_p, high_p, low_p, close_p)

                    if is_strategy_new_valid:
                        key_new = f"{symbol}_{tf}_{candles[-3]['time']}_strat_new"
                        if key_new not in sent_alerts:
                            sent_alerts[key_new] = True
                            msg = f"🚀 *تنبيه (الاستراتيجية الجديدة - ابلاع بشمعة ذات ذيل سفلي)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg)
                            print(f"🚨 [إشارة الاستراتيجية الجديدة] تم إرسال تنبيه لـ {symbol.upper()} - {tf}", flush=True)

                    time.sleep(0.01)

            print(f"✅ اكتملت الدورة رقم {cycle} لـ 500 عملة", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
