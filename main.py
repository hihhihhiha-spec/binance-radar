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

print("🔥 [إقلاع النظام] بدأ تشغيل الرادار على Bybit...", flush=True)

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
        self.wfile.write(b"Bybit Custom Strategy Radar is Active")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

sent_alerts = {}

# ترويسات متصفح وهمية متكاملة تماماً لتجاوز حظر Cloudflare الخاص بـ Bybit
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.bybit.com/"
}

def get_top_futures_symbols(limit=500):
    try:
        print("🔍 [Bybit] جاري جلب قائمة العملات...", flush=True)
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        
        # استخدام Session للحفاظ على الكوكيز وتجاوز الحماية
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=12)
        
        print(f"📡 حالة الاستجابة من Bybit: {response.status_code}", flush=True)
        
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
            print(f"🔥 [نجاح Bybit] تم جلب واعتماد {len(top_symbols)} عملة للفحص.", flush=True)
            return top_symbols
        else:
            print(f"⚠️ خطأ Bybit (كود الاستجابة): {response.status_code}", flush=True)
    except Exception as e:
        print(f"❌ خطأ جلب العملات من Bybit: {e}", flush=True)
    return []

BYBIT_INTERVALS = {'1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30', '1h': '60', '4h': '240'}

def get_klines(symbol, interval, limit=25):
    try:
        bybit_tf = BYBIT_INTERVALS.get(interval, '60')
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol.upper()}&interval={bybit_tf}&limit={limit}"
        
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=6)
        
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
    print("🟢 [رادار بايبت] بدأ العمل وتفعيل الطباعة الفورية...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار على منصة Bybit بنجاح.")

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
                    print("⚠️ لم يتم جلب العملات، إعادة المحاولة خلال 30 ثانية...", flush=True)
                    time.sleep(30)
                    continue

            print(f"\n🔄 [دورة رقم {cycle}] فحص {len(symbols)} عملة على Bybit...", flush=True)

            for idx, symbol in enumerate(symbols):
                print(f"🔍 [فحص] {symbol.upper()}...", flush=True)
                
                for tf in timeframes:
                    candles = get_klines(symbol, tf, limit=25)
                    if not candles or len(candles) < 15:
                        continue
                    
                    # --- شرط: منطقة التجميع بعيدة عن القمة ---
                    try:
                        recent_highs = [c['h'] for c in candles[-15:-5]]
                        is_far_from_peak = candles[-5]['h'] <= max(recent_highs)
                    except:
                        is_far_from_peak = True

                    if not is_far_from_peak:
                        print(f"    ❌ [{symbol.upper()} | {tf}] استبعاد: قريبة من القمة", flush=True)
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
                        print(f"    ❌ [{symbol.upper()} | {tf}] استبعاد C1", flush=True)
                        continue

                    # 2. الشمعة الثانية
                    cond_c2 = (
                        c2_val < o2 and
                        c2_val < l1 and
                        (total_len2 * 0.40 <= b2 <= total_len2 * 0.60) and
                        (total_len2 * 0.01 <= lw2 <= total_len2 * 0.35) and
                        (total_len2 * 0.01 <= uw2 <= total_len2 * 0.15)
                    )

                    if not cond_c2:
                        print(f"    ❌ [{symbol.upper()} | {tf}] استبعاد C2", flush=True)
                        continue

                    # 3. الشمعة الثالثة
                    cond_c3 = (
                        c3_val > o3 and
                        l2 <= c3_val <= h2 and
                        lw3 < lw2
                    )

                    if not cond_c3:
                        print(f"    ❌ [{symbol.upper()} | {tf}] استبعاد C3", flush=True)
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
                            msg = f"⭐ *إشارة الاستراتيجية المخصصة (Bybit)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg)
                            print(f"🚨 [إشارة مطابقة ناجحة] {symbol.upper()} | {tf}", flush=True)
                    else:
                        print(f"    ❌ [{symbol.upper()} | {tf}] استبعاد - التجميع/الكسر", flush=True)

                    time.sleep(0.005)

            print(f"✅ اكتملت الدورة رقم {cycle} لـ 500 عملة", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ عام: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
