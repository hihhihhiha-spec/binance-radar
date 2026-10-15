import sys
import json
import time
import os
import threading
import requests
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- تفعيل الطباعة الفورية اللحظية ---
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
        self.wfile.write(b"Single Custom Strategy Radar is Active")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

sent_alerts = {}
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# --- قائمة الـ 100 عملة المكتوبة صراحة داخل الكود ---
EXPLICIT_SYMBOLS = [
    "btcusdt", "ethusdt", "solusdt", "xrpusdt", "dogeusdt", "adausdt", "avaxusdt", "linkusdt", "suiusdt", "bnbusdt",
    "nearusdt", "pepeusdt", "wifusdt", "renderusdt", "fetusdt", "bonkusdt", "flokiusdt", "shibusdt", "arbusdt", "opusdt",
    "aptusdt", "injusdt", "ftmusdt", "grtusdt", "uniusdt", "aaveusdt", "ldousdt", "pendleusdt", "tiausdt", "seiust",
    "blurusdt", "atomusdt", "dotusdt", "xlmusdt", "ltcusdt", "bchusdt", "etcusdt", "filusdt", "hbarusdt", "galausdt",
    "thetausdt", "egldusdt", "flowusdt", "chzusdt", "sandusdt", "manausdt", "axsusdt", "enjusdt", "runeusdt", "kavausdt",
    "compusdt", "snxusdt", "crvusdt", "batusdt", "zrxusdt", "sushiusdt", "1inchusdt", "ankrusdt", "oceanusdt", "ctsiusdt",
    "qtumusdt", "iostusdt", "zilusdt", "wavesusdt", "icxusdt", "omgusdt", "zenusdt", "rvnusdt", "coreusdt", "notusdt",
    "bomeusdt", "slerfusdt", "peopleusdt", "omdusdt", "rsrusdt", "cotiusdt", "kncusdt", "straxusdt", "sysusdt", "celrusdt",
    "chrusdt", "aliceusdt", "tlmusdt", "reefusdt", "pundixusdt", "stptusdt", "dgbusdt", "ognusdt", "alphausdt", "phausdt",
    "zecusdt", "dashusdt", "scusdt", "jstusdt", "sunusdt", "dentusdt", "hotusdt", "mtlusdt", "ognusdt", "wavesusdt"
]

BYBIT_INTERVALS = {'1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30', '1h': '60', '4h': '240'}

def get_klines(symbol, interval, limit=25):
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

def main():
    print("🟢 [رادار الاستراتيجية المخصصة - قائمة صريحة] بدأ العمل والطباعة الحية مفعلة...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار بنجاح باستخدام قائمة العملات المكتوبة صراحة.")

    timeframes = ['1m', '5m', '15m', '30m', '1h', '4h']
    symbols = EXPLICIT_SYMBOLS
    cycle = 1

    while True:
        try:
            print(f"\n🔄 [بدء الدورة رقم {cycle}] جاري فحص {len(symbols)} عملة مدرجة صراحةً...", flush=True)

            for idx, symbol in enumerate(symbols):
                print(f"➡️ [{idx+1}/{len(symbols)}] فحص العملة: {symbol.upper()}", flush=True)
                
                for tf in timeframes:
                    candles = get_klines(symbol, tf, limit=25)
                    if not candles or len(candles) < 15:
                        continue
                    
                    try:
                        recent_highs = [c['h'] for c in candles[-15:-5]]
                        is_far_from_peak = candles[-5]['h'] <= max(recent_highs)
                    except:
                        is_far_from_peak = True

                    if not is_far_from_peak:
                        continue

                    c1, c2, c3 = candles[-6], candles[-5], candles[-4]
                    
                    o1, h1, l1, c1_val = c1['o'], c1['h'], c1['l'], c1['c']
                    o2, h2, l2, c2_val = c2['o'], c2['h'], c2['l'], c2['c']
                    o3, h3, l3, c3_val = c3['o'], c3['h'], c3['l'], c3['c']

                    total_len1 = h1 - l1
                    total_len2 = h2 - l2

                    if total_len1 <= 0 or total_len2 <= 0:
                        continue

                    b1 = abs(o1 - c1_val)
                    uw1 = h1 - max(o1, c1_val)
                    lw1 = min(o1, c1_val) - l1

                    b2 = abs(o2 - c2_val)
                    uw2 = h2 - max(o2, c2_val)
                    lw2 = min(o2, c2_val) - l2

                    lw3 = min(o3, c3_val) - l3

                    # 1. مواصفات الشمعة الأولى
                    cond_c1 = (
                        (total_len1 * 0.50 <= b1 <= total_len1 * 0.70) and
                        (total_len1 * 0.01 <= lw1 <= total_len1 * 0.35) and
                        (total_len1 * 0.01 <= uw1 <= total_len1 * 0.15)
                    )
                    if not cond_c1:
                        continue

                    # 2. مواصفات الشمعة الثانية
                    cond_c2 = (
                        c2_val < o2 and 
                        c2_val < l1 and 
                        (total_len2 * 0.40 <= b2 <= total_len2 * 0.60) and 
                        (total_len2 * 0.01 <= lw2 <= total_len2 * 0.35) and 
                        (total_len2 * 0.01 <= uw2 <= total_len2 * 0.15)
                    )
                    if not cond_c2:
                        continue

                    # 3. مواصفات الشمعة الثالثة
                    cond_c3 = (
                        c3_val > o3 and 
                        l2 <= c3_val <= h2 and 
                        lw3 < lw2
                    )
                    if not cond_c3:
                        continue

                    # 4. التجميع والكسر
                    subsequent_candles = candles[-3:-1]
                    consolidation_ok = True
                    breakout_found = False

                    for sc in subsequent_candles:
                        if sc['l'] < l2 or sc['h'] > h2:
                            if sc['c'] > o2 and sc['c'] > h2:
                                breakout_found = True
                            else:
                                consolidation_ok = False

                    latest_c = candles[-2]
                    if not breakout_found and latest_c['c'] > h2 and latest_c['c'] > latest_c['o']:
                        breakout_found = True

                    if consolidation_ok and breakout_found:
                        key = f"{symbol}_{tf}_{latest_c['time']}_custom_strategy"
                        if key not in sent_alerts:
                            sent_alerts[key] = True
                            msg = f"⭐ *إشارة الاستراتيجية المخصصة*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg)
                            print(f"🚨 [إشارة مطابقة ناجحة وتم الإرسال] {symbol.upper()} | {tf}", flush=True)

                    time.sleep(0.005)

            print(f"✅ [اكتملت الدورة رقم {cycle}] جاري البدء في الدورة التالية...", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ عام في الحلقة: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
