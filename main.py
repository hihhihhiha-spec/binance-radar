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
        self.wfile.write(b"Dual Strategy Radar - Dual C2 Pattern Active")
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
    print("🟢 [رادار الاستراتيجيتين - دعم المطرقة + الشمعة الحمراء الممتلئة] بدأ العمل...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار (مع دمج شمعة المطرقة والشمعة الحمراء ذات الجسم الممتلئ والذيل السفلي).")

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

            print(f"\n🔄 [دورة رقم {cycle}] فحص {len(symbols)} عملة وطباعة تفاصيل الفحص...", flush=True)

            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    
                    print(f"🔍 [يفحص الآن] العملة: {symbol.upper()} | الفريم: {tf}", flush=True)

                    candles = get_klines(symbol, tf, limit=10)
                    if not candles or len(candles) < 5:
                        print(f"   ⚠️ [استبعاد] بيانات الشموع غير كافية لـ {symbol.upper()} على {tf}", flush=True)
                        continue
                    
                    c1, c2, c3, c4 = candles[-5], candles[-4], candles[-3], candles[-2]
                    
                    # ==================== [فحص الاستراتيجية الأولى] ====================
                    sc1, sc2, sc3 = candles[-4], candles[-3], candles[-2]
                    o1, h1, l1, cl1 = sc1['o'], sc1['h'], sc1['l'], sc1['c']
                    o2, h2, l2, cl2 = sc2['o'], sc2['h'], sc2['l'], sc2['c']
                    o3, h3, l3, cl3 = sc3['o'], sc3['h'], sc3['l'], sc3['c']

                    body1, u_wick1, l_wick1 = get_wick_body(o1, h1, l1, cl1)
                    body2, u_wick2, l_wick2 = get_wick_body(o2, h2, l2, cl2)

                    min_c1_u_wick = body1 * 0.05
                    max_c2_u_wick = body2 * 0.05
                    min_c2_l_wick = body2 * 0.05

                    c1_ok = (cl1 < o1 and u_wick1 > min_c1_u_wick)
                    c2_ok = (cl2 < o2 and u_wick2 <= max_c2_u_wick and l_wick2 > min_c2_l_wick)
                    c3_ok = (cl3 > o3 and (l3 >= l1 and h3 <= h1) and (l3 >= l2 and cl3 > h2))

                    if c1_ok and c2_ok and c3_ok:
                        key1 = f"{symbol}_{tf}_{sc3['time']}_strategy1"
                        if key1 not in sent_alerts:
                            sent_alerts[key1] = True
                            msg1 = f"⭐ *تنبيه الاستراتيجية الأولى*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg1)
                            print(f"🚨 [إشارة مطابقة 1] تم إرسال تنبيه لـ {symbol.upper()} على فريم {tf}", flush=True)

                    # ==================== [فحص الاستراتيجية الثانية (المطرقة أو الشمعة الحمراء الممتلئة)] ====================
                    to1, th1, tl1, tc1 = c1['o'], c1['h'], c1['l'], c1['c']
                    to2, th2, tl2, tc2 = c2['o'], c2['h'], c2['l'], c2['c']
                    to3, th3, tl3, tc3 = c3['o'], c3['h'], c3['l'], c3['c']
                    to4, th4, tl4, tc4 = c4['o'], c4['h'], c4['l'], c4['c']

                    total_len1 = th1 - tl1
                    if total_len1 > 0:
                        body_sz1 = abs(to1 - tc1)
                        body_pct1 = (body_sz1 / total_len1) * 100
                        lower_pct1 = (l_wick_calc(to1, th1, tl1, tc1) / total_len1) * 100
                        upper_pct1 = (u_wick_calc(to1, th1, tl1, tc1) / total_len1) * 100
                        s2_c1_valid = (50 <= body_pct1 <= 70) and (20 <= lower_pct1 <= 35) and (5 <= upper_pct1 <= 15)
                    else:
                        s2_c1_valid = False

                    total_len2 = th2 - tl2
                    if total_len2 > 0 and tc2 < to2:
                        body_sz2 = abs(to2 - tc2)
                        body_pct2 = (body_sz2 / total_len2) * 100
                        lower_pct2 = (l_wick_calc(to2, th2, tl2, tc2) / total_len2) * 100
                        upper_pct2 = (u_wick_calc(to2, th2, tl2, tc2) / total_len2) * 100

                        # 1) الشرط القديم: شمعة المطرقة المرنة
                        is_hammer = (15 <= body_pct2 <= 30) and (40 <= lower_pct2 <= 80) and (0 <= upper_pct2 <= 3)
                        
                        # 2) الشرط الجديد: شمعة حمراء ذات جسم ممتلئ أكبر من ذيلها السفلي (جسم كبير + ذيل سفلي فقط/أو صغير)
                        is_filled_red_with_lower_wick = (body_pct2 >= 50) and (lower_pct2 > 0) and (body_pct2 > lower_pct2) and (upper_pct2 <= 2)

                        # الشمعة الثانية مقبولة إذا تحققت المطرقة أو الشمعة الحمراء الممتلئة
                        s2_c2_valid = is_hammer or is_filled_red_with_lower_wick
                        
                        s2_price_break = (tc2 < tl1)
                    else:
                        s2_c2_valid = False
                        s2_price_break = False

                    lw3 = l_wick_calc(to3, th3, tl3, tc3)
                    lw2 = l_wick_calc(to2, th2, tl2, tc2)
                    s2_c3_valid = (tc3 > to3) and (abs(to3 - tc2) <= (th2 - tl2) * 0.05) and (tc3 > th2) and (lw3 < lw2)
                    s2_c4_valid = (tc4 > to4)

                    if not (s2_c1_valid and s2_c2_valid and s2_price_break and s2_c3_valid and s2_c4_valid):
                        print(f"   ❌ [استبعاد S2 لـ {symbol.upper()} | {tf}] C1:{s2_c1_valid} | C2(Hammer/FilledRed):{s2_c2_valid} | Break:{s2_price_break} | C3:{s2_c3_valid} | C4:{s2_c4_valid}", flush=True)
                    else:
                        key2 = f"{symbol}_{tf}_{c4['time']}_strategy2"
                        if key2 not in sent_alerts:
                            sent_alerts[key2] = True
                            msg2 = f"⭐ *تنبيه الاستراتيجية الثانية (متقدمة - مطرقة أو شمعة ممتلئة)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg2)
                            print(f"🚨 [إشارة مطابقة 2] تم إرسال تنبيه لـ {symbol.upper()} على فريم {tf}", flush=True)

                    time.sleep(0.005)

            print(f"✅ اكتملت الدورة رقم {cycle} لـ 500 عملة", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ: {e}", flush=True)
            time.sleep(10)

def l_wick_calc(o, h, l, c):
    return min(o, c) - l

def u_wick_calc(o, h, l, c):
    return h - max(o, c)

if __name__ == "__main__":
    main()
