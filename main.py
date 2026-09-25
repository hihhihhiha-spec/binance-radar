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
        self.wfile.write(b"Dual Strategies Radar with Exact Rules is Active")
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

def main():
    print("🟢 [رادار الاستراتيجيتين - الشروط الدقيقة الجديدة] بدأ العمل...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار بالاستراتيجيتين والشروط الجديدة.")

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

            print(f"\n🔄 [دورة رقم {cycle}] فحص {len(symbols)} عملة للاستراتيجيتين...", flush=True)

            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    candles = get_klines(symbol, tf, limit=10)
                    if not candles or len(candles) < 5:
                        continue
                    
                    # ==================== [فحص الاستراتيجية الأولى] ====================
                    c1_s1, c2_s1, c3_s1 = candles[-4], candles[-3], candles[-2]
                    o1, h1, l1, cl1 = c1_s1['o'], c1_s1['h'], c1_s1['l'], c1_s1['c']
                    o2, h2, l2, cl2 = c2_s1['o'], c2_s1['h'], c2_s1['l'], c2_s1['c']
                    o3, h3, l3, cl3 = c3_s1['o'], c3_s1['h'], c3_s1['l'], c3_s1['c']

                    body1, u_wick1, l_wick1 = get_wick_body(o1, h1, l1, cl1)
                    body2, u_wick2, l_wick2 = get_wick_body(o2, h2, l2, cl2)
                    body3, u_wick3, l_wick3 = get_wick_body(o3, h3, l3, cl3)

                    min_c1_u_wick = body1 * 0.05
                    c1_ok = (cl1 < o1 and u_wick1 > min_c1_u_wick)

                    max_c2_u_wick = body2 * 0.05
                    min_c2_l_wick = body2 * 0.05
                    c2_ok = (cl2 < o2 and u_wick2 <= max_c2_u_wick and l_wick2 > min_c2_l_wick)

                    c3_ok = (cl3 > o3 and (l3 >= l1 and h3 <= h1) and (l3 >= l2 and cl3 > h2))

                    if c1_ok and c2_ok and c3_ok:
                        key1 = f"{symbol}_{tf}_{c3_s1['time']}_strategy1"
                        if key1 not in sent_alerts:
                            sent_alerts[key1] = True
                            msg1 = f"⭐ *تنبيه الاستراتيجية الأولى*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg1)
                            print(f"🚨 [إشارة مطابقة 1] تم إرسال تنبيه لـ {symbol.upper()} على فريم {tf}", flush=True)
                    else:
                        print(f"    ❌ [استبعاد S1 لـ {symbol.upper()} | {tf}] C1:{c1_ok} | C2:{c2_ok} | C3:{c3_ok}", flush=True)

                    # ==================== [فحص الاستراتيجية الثانية الجديدة] ====================
                    # تتطلب 3 شموع متتالية: C1 (الأولى)، C2 (الثانية)، C3 (الثالثة الخضراء)
                    s2_c1, s2_c2, s2_c3 = candles[-4], candles[-3], candles[-2]
                    
                    to1, th1, tl1, tc1 = s2_c1['o'], s2_c1['h'], s2_c1['l'], s2_c1['c']
                    to2, th2, tl2, tc2 = s2_c2['o'], s2_c2['h'], s2_c2['l'], s2_c2['c']
                    to3, th3, tl3, tc3 = s2_c3['o'], s2_c3['h'], s2_c3['l'], s2_c3['c']

                    total_len1 = th1 - tl1
                    total_len2 = th2 - tl2

                    if total_len1 > 0 and total_len2 > 0:
                        b1 = abs(to1 - tc1)
                        uw1 = th1 - max(to1, tc1)
                        lw1 = min(to1, tc1) - tl1

                        b2 = abs(to2 - tc2)
                        uw2 = th2 - max(to2, tc2)
                        lw2 = min(to2, tc2) - tl2

                        # شروط الشمعة الأولى للاستراتيجية الثانية:
                        # حمراء هابطة، جسمها >= 50%، ديلها العلوي <= 20%، ديلها السفلي <= 30%
                        cond1_dir = (tc1 < to1)
                        cond1_body = (b1 >= total_len1 * 0.50)
                        cond1_uw = (uw1 <= total_len1 * 0.20)
                        cond1_lw = (lw1 <= total_len1 * 0.30)
                        s2_c1_valid = cond1_dir and cond1_body and cond1_uw and cond1_lw

                        # شروط الشمعة الثانية للاستراتيجية الثانية:
                        # حمراء هابطة، تكسر الأولى وتغلق تحت ذيلها السفلي، جسمها >= 50%، ديلها العلوي <= 3%, ديلها السفلي <= 30%
                        cond2_dir = (tc2 < to2)
                        cond2_break = (tc2 < tl1)  # تغلق تحت ذيل الأولى السفلي
                        cond2_body = (b2 >= total_len2 * 0.50)
                        cond2_uw = (uw2 <= total_len2 * 0.03)
                        cond2_lw = (lw2 <= total_len2 * 0.30)
                        s2_c2_valid = cond2_dir and cond2_break and cond2_body and cond2_uw and cond2_lw

                        # شروط الشمعة الثالثة للاستراتيجية الثانية:
                        # خضراء، تكسر الشمعة الثانية وتغلق فوقها (فوق قمة الثانية)
                        cond3_dir = (tc3 > to3)
                        cond3_break = (tc3 > th2)
                        s2_c3_valid = cond3_dir and cond3_break

                        if s2_c1_valid and s2_c2_valid and s2_c3_valid:
                            key2 = f"{symbol}_{tf}_{s2_c3['time']}_strategy2_new"
                            if key2 not in sent_alerts:
                                sent_alerts[key2] = True
                                msg2 = f"⭐ *تنبيه الاستراتيجية الثانية الجديدة*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                                send_telegram_message(msg2)
                                print(f"🚨 [إشارة مطابقة 2] تم إرسال تنبيه الاستراتيجية الثانية لـ {symbol.upper()} على فريم {tf}", flush=True)
                        else:
                            print(f"    ❌ [استبعاد S2 لـ {symbol.upper()} | {tf}] C1_Valid:{s2_c1_valid} | C2_Valid:{s2_c2_valid} | C3_Valid:{s2_c3_valid}", flush=True)
                    else:
                        print(f"    ⚠️ [استبعاد S2] طول الشموع صفرية لـ {symbol.upper()} على {tf}", flush=True)

                    time.sleep(0.005)

            print(f"✅ اكتملت الدورة رقم {cycle} لـ 500 عملة", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
