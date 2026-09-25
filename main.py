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
        self.wfile.write(b"Full Diagnostic Radar Active")
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

def l_wick_calc(o, h, l, c):
    return min(o, c) - l

def u_wick_calc(o, h, l, c):
    return h - max(o, c)

def main():
    print("🟢 [رادار الفحص الحي الشامل] بدأ العمل...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار مع تفعيل طباعة الفحص الحي للعملات.")

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

            print(f"\n🔄 [دورة رقم {cycle}] بدء فحص العملات والفريمات...", flush=True)

            for idx, symbol in enumerate(symbols):
                for tf in timeframes:

                    candles = get_klines(symbol, tf, limit=10)
                    if not candles or len(candles) < 5:
                        continue
                    
                    c1, c2, c3 = candles[-4], candles[-3], candles[-2]
                    
                    # ==================== [فحص الاستراتيجية الثانية] ====================
                    to1, th1, tl1, tc1 = c1['o'], c1['h'], c1['l'], c1['c']
                    to2, th2, tl2, tc2 = c2['o'], c2['h'], c2['l'], c2['c']
                    to3, th3, tl3, tc3 = c3['o'], c3['h'], c3['l'], c3['c']

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

                        is_hammer = (15 <= body_pct2 <= 30) and (40 <= lower_pct2 <= 80) and (0 <= upper_pct2 <= 3)
                        is_filled_red_with_lower_wick = (body_pct2 >= 50) and (lower_pct2 > 0) and (body_pct2 > lower_pct2) and (upper_pct2 <= 2)

                        s2_c2_valid = is_hammer or is_filled_red_with_lower_wick
                        s2_price_break = (tc2 < tl1)
                    else:
                        s2_c2_valid = False
                        s2_price_break = False

                    lw3 = l_wick_calc(to3, th3, tl3, tc3)
                    lw2 = l_wick_calc(to2, th2, tl2, tc2)
                    s2_c3_valid = (tc3 > to3) and (abs(to3 - tc2) <= (th2 - tl2) * 0.05) and (tc3 > th2) and (lw3 < lw2)

                    # طباعة حالة الفحص لكل عملة وفريم بشكل مباشر لتراها بنفسك
                    print(f"🔍 فحص {symbol.upper()} [{tf}] -> الشمعة الأولى: {s2_c1_valid} | الشمعة الثانية: {s2_c2_valid} | كسر القاع: {s2_price_break} | الشمعة الثالثة: {s2_c3_valid}", flush=True)

                    if s2_c1_valid and s2_c2_valid and s2_price_break and s2_c3_valid:
                        key2 = f"{symbol}_{tf}_{c3['time']}_strategy2"
                        if key2 not in sent_alerts:
                            sent_alerts[key2] = True
                            msg2 = f"⭐ *تنبيه الاستراتيجية الثانية (3 شموع)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg2)
                            print(f"🚨 [إشارة مطابقة 2] تم إرسال تنبيه لـ {symbol.upper()} على فريم {tf}", flush=True)

                    time.sleep(0.005)

            print(f"✅ اكتملت الدورة رقم {cycle} لـ 500 عملة", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
