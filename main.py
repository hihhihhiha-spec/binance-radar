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
        self.wfile.write(b"Four Strategies Radar with Trend Filter is Active")
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

def get_klines(symbol, interval, limit=20):
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
    print("🟢 [رادار الاستراتيجيات الأربع مع شرط الاتجاه الهابط] بدأ العمل...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار بالاستراتيجيات الأربع مع فلتر الاتجاه الهابط.")

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

            print(f"\n🔄 [دورة رقم {cycle}] فحص {len(symbols)} عملة للاستراتيجيات الأربع...", flush=True)

            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    candles = get_klines(symbol, tf, limit=20)
                    if not candles or len(candles) < 16:
                        continue
                    
                    # --- فلتر الاتجاه الهابط السابق (Price Action) ---
                    # شروط الاتجاه الهابط: أن يكون سعر افتتاح الشمعة الأولى أقل من متوسط أسعار الشموع السابقة
                    close_prices_list = [c['c'] for c in candles]
                    # نفترض أن الشمعة الأولى للنماذج تقع في الفهرس -5 أو -6، نتحقق من الاتجاه العام قبلها
                    # بناءً على طلبك: close_p[4] < sum(close_p[5:15]) / 10
                    # في بايثون، لنأخذ الشموع بشكل آمن:
                    try:
                        # سنفحص الاتجاه الهابط العام بناءً على الشمعة الأولى للنموذج (نعتبرها الفهرس المناسب)
                        downtrend_ok = candles[-5]['o'] < (sum(close_prices_list[-15:-5]) / 10)
                    except:
                        downtrend_ok = True  # تجاوز آمن في حال عدم كفاية البيانات

                    if not downtrend_ok:
                        continue  # إذا لم تكن في اتجاه هابط، يتم تخطي فحص الاستراتيجيات لهذه العملة والفريم

                    # تجهيز الشموع المشتركة للنماذج
                    c1, c2, c3, c4, c5 = candles[-6], candles[-5], candles[-4], candles[-3], candles[-2]
                    
                    o1, h1, l1, c1_val = c1['o'], c1['h'], c1['l'], c1['c']
                    o2, h2, l2, c2_val = c2['o'], c2['h'], c2['l'], c2['c']
                    o3, h3, l3, c3_val = c3['o'], c3['h'], c3['l'], c3['c']
                    o4, h4, l4, c4_val = c4['o'], c4['h'], c4['l'], c4['c']
                    o5, h5, l5, c5_val = c5['o'], c5['h'], c5['l'], c5['c']

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

                    # الشروط المشتركة للشمعة الأولى في كل الاستراتيجيات الأربع:
                    # جسم 50%-70%، ديل سفلي 20%-35%، ديل علوي 5%-15%
                    common_c1 = (
                        (total_len1 * 0.50 <= b1 <= total_len1 * 0.70) and
                        (total_len1 * 0.20 <= lw1 <= total_len1 * 0.35) and
                        (total_len1 * 0.05 <= uw1 <= total_len1 * 0.15)
                    )

                    min_rng = min(l1, l2, l3)
                    max_rng = max(h1, h2, h3)

                    # ==================== [الاستراتيجية الأولى] ====================
                    if common_c1:
                        s1_c2 = (
                            c2_val < o2 and
                            b2 >= total_len2 * 0.20 and
                            (total_len2 * 0.20 <= lw2 <= total_len2 * 0.50) and
                            uw2 < total_len2 * 0.01 and
                            (l1 <= l2 <= h1) and  # داخل الشمعة الأولى
                            l2 < l1               # ديل الشمعة الثانية أسفل ديل الشمعة الأولى
                        )
                        s1_c3 = (
                            c3_val > o3 and
                            c3_val > h2 and
                            lw3 < lw2
                        )
                        s1_c4 = (l4 >= min_rng and h4 <= max_rng)
                        s1_c5 = (c5_val > o5 and c5_val > h1)

                        if s1_c2 and s1_c3 and s1_c4 and s1_c5:
                            key1 = f"{symbol}_{tf}_{c5['time']}_strategy1"
                            if key1 not in sent_alerts:
                                sent_alerts[key1] = True
                                msg1 = f"⭐ *تنبيه الاستراتيجية الأولى*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                                send_telegram_message(msg1)
                                print(f"🚨 [إشارة مطابقة 1] تم إرسال تنبيه لـ {symbol.upper()} على فريم {tf}", flush=True)
                        else:
                            print(f"    ❌ [استبعاد S1 لـ {symbol.upper()} | {tf}]", flush=True)

                    # ==================== [الاستراتيجية الثانية] ====================
                    if common_c1:
                        s2_c2 = (
                            c2_val < o2 and
                            c2_val < l1 and  # كسر قاع الأولى واغلاق تحته تماماً
                            (total_len2 * 0.15 <= b2 <= total_len2 * 0.30) and
                            (total_len2 * 0.60 <= lw2 <= total_len2 * 0.75) and
                            (total_len2 * 0.00 <= uw2 <= total_len2 * 0.01)
                        )
                        s2_c3 = (
                            c3_val > o3 and
                            c3_val > h2 and
                            lw3 < lw2
                        )
                        s2_c4 = (l4 >= min_rng and h4 <= max_rng)
                        # شمعة خامسة خضراء تكسر النطاق وتغلق فوقه تماماً
                        s2_c5 = (c5_val > o5 and c5_val > h1)

                        if s2_c2 and s2_c3 and s2_c4 and s2_c5:
                            key2 = f"{symbol}_{tf}_{c5['time']}_strategy2"
                            if key2 not in sent_alerts:
                                sent_alerts[key2] = True
                                msg2 = f"⭐ *تنبيه الاستراتيجية الثانية*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                                send_telegram_message(msg2)
                                print(f"🚨 [إشارة مطابقة 2] تم إرسال تنبيه الاستراتيجية الثانية لـ {symbol.upper()} على فريم {tf}", flush=True)
                        else:
                            print(f"    ❌ [استبعاد S2 لـ {symbol.upper()} | {tf}]", flush=True)

                    # ==================== [الاستراتيجية الثالثة] ====================
                    if common_c1:
                        s3_c2 = (
                            c2_val < o2 and
                            c2_val < l1 and  # كسر قاع الشمعة الأولى
                            (total_len2 * 0.45 <= b2 <= total_len2 * 0.55) and  # تقريباً 50%
                            (total_len2 * 0.20 <= lw2 <= total_len2 * 0.35) and
                            (total_len2 * 0.05 <= uw2 <= total_len2 * 0.15)
                        )
                        s3_c3 = (
                            c3_val > o3 and
                            c3_val > h2 and
                            lw3 < lw2
                        )
                        s3_c4 = (l4 >= min_rng and h4 <= max_rng)
                        s3_c5 = (c5_val > o5 and c5_val > h1)

                        if s3_c2 and s3_c3 and s3_c4 and s3_c5:
                            key3 = f"{symbol}_{tf}_{c5['time']}_strategy3"
                            if key3 not in sent_alerts:
                                sent_alerts[key3] = True
                                msg3 = f"⭐ *تنبيه الاستراتيجية الثالثة*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                                send_telegram_message(msg3)
                                print(f"🚨 [إشارة مطابقة 3] تم إرسال تنبيه الاستراتيجية الثالثة لـ {symbol.upper()} على فريم {tf}", flush=True)
                        else:
                            print(f"    ❌ [استبعاد S3 لـ {symbol.upper()} | {tf}]", flush=True)

                    # ==================== [الاستراتيجية الرابعة] ====================
                    if common_c1:
                        s4_c2 = (
                            c2_val < o2 and
                            c2_val < l1 and  # كسر قاع الشمعة الأولى
                            b2 >= total_len2 * 0.30 and  # 30% أو أكثر
                            (total_len2 * 0.20 <= lw2 <= total_len2 * 0.35) and
                            uw2 < total_len2 * 0.15      # أقل من 15%
                        )
                        s4_c3 = (
                            c3_val > o3 and
                            (l3 >= min_rng and h3 <= max_rng) and  # داخل النطاق
                            lw3 < lw2
                        )
                        s4_c4 = (l4 >= min_rng and h4 <= max_rng)
                        s4_c5 = (c5_val > o5 and c5_val > h1)

                        if s4_c2 and s4_c3 and s4_c4 and s4_c5:
                            key4 = f"{symbol}_{tf}_{c5['time']}_strategy4"
                            if key4 not in sent_alerts:
                                sent_alerts[key4] = True
                                msg4 = f"⭐ *تنبيه الاستراتيجية الرابعة*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                                send_telegram_message(msg4)
                                print(f"🚨 [إشارة مطابقة 4] تم إرسال تنبيه الاستراتيجية الرابعة لـ {symbol.upper()} على فريم {tf}", flush=True)
                        else:
                            print(f"    ❌ [استبعاد S4 لـ {symbol.upper()} | {tf}]", flush=True)

                    time.sleep(0.005)

            print(f"✅ اكتملت الدورة رقم {cycle} لـ 500 عملة", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
