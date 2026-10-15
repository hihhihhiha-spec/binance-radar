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
        self.wfile.write(b"Optimized Custom Strategy Radar with Full Logging is Active")
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
    print("🟢 [رادار الاستراتيجية المرن مع الطباعة الكاملة] بدأ العمل...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار بالنسخة المرنة (مع تفعيل سجلات الطباعة التفصيلية).")

    timeframes = ['1m', '5m', '15m', '30m', '1h', '4h']
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

            print(f"\n🔄 [دورة رقم {cycle}] فحص {len(symbols)} عملة بالنسخة المرنة...", flush=True)

            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    candles = get_klines(symbol, tf, limit=25)
                    if not candles or len(candles) < 15:
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

                    # 1. شروط الشمعة الأولى
                    cond_c1 = (
                        (b1 >= total_len1 * 0.40) and
                        (lw1 >= total_len1 * 0.01) and
                        (uw1 >= total_len1 * 0.01)
                    )

                    if not cond_c1:
                        print(f"    ❌ [استبعاد C1] {symbol.upper()} | {tf}", flush=True)
                        continue

                    # 2. الشمعة الثانية
                    cond_c2 = (
                        c2_val < o2 and
                        c2_val < l1
                    )

                    if not cond_c2:
                        print(f"    ❌ [استبعاد C2 (لم تكسر القاع أو ليست حمراء)] {symbol.upper()} | {tf}", flush=True)
                        continue

                    # 3. الشمعة الثالثة
                    cond_c3 = (
                        c3_val > o3 and
                        l2 <= c3_val <= h2
                    )

                    if not cond_c3:
                        print(f"    ❌ [استبعاد C3 (خارج نطاق الثانية)] {symbol.upper()} | {tf}", flush=True)
                        continue

                    # 4. التجميع والكسر
                    latest_c = candles[-2]
                    breakout_found = (latest_c['c'] > latest_c['o'] and latest_c['c'] > h2)

                    if breakout_found:
                        key = f"{symbol}_{tf}_{latest_c['time']}_custom_strategy_opt"
                        if key not in sent_alerts:
                            sent_alerts[key] = True
                            msg = f"⭐ *إشارة قوية مطابقة للرادار*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg)
                            print(f"🚨 [إشارة مطابقة مؤكدة وبجاح] {symbol.upper()} | {tf}", flush=True)
                    else:
                        print(f"    ❌ [استبعاد - بانتظار الكسر الصعودي الصحيح] {symbol.upper()} | {tf}", flush=True)

                    time.sleep(0.005)

            print(f"✅ اكتملت الدورة رقم {cycle} لـ 500 عملة", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ عام: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
