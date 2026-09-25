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
        self.wfile.write(b"Dual Strategy Radar Active")
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

BYBIT_INTERVALS = {
    '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30', 
    '1h': '60', '2h': '120', '4h': '240', '6h': '360', '12h': '720', '1d': 'D'
}

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
    print("🟢 [رادار الاستراتيجيتين - شامل كافة الفريمات] بدأ العمل...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل الرادار بكافة الفريمات (الاستراتيجية الأولى بشروطها الأصلية + الثانية بمرونتها الجديدة).")

    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
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

            print(f"\n🔄 [دورة رقم {cycle}] فحص جميع العملات على كافة الفريمات...", flush=True)

            for idx, symbol in enumerate(symbols):
                for tf in timeframes:

                    candles = get_klines(symbol, tf, limit=10)
                    if not candles or len(candles) < 5:
                        continue
                    
                    c1, c2, c3 = candles[-4], candles[-3], candles[-2]
                    
                    to1, th1, tl1, tc1 = c1['o'], c1['h'], c1['l'], c1['c']
                    to2, th2, tl2, tc2 = c2['o'], c2['h'], c2['l'], c2['c']
                    to3, th3, tl3, tc3 = c3['o'], c3['h'], c3['l'], c3['c']

                    # ==================== [الاستراتيجية الأولى - شروطها الأصلية الصارمة] ====================
                    s1_c1_red = (tc1 < to1)
                    s1_c2_red = (tc2 < to2)
                    
                    body1_s1 = abs(tc1 - to1)
                    wicks1_s1 = (th1 - max(to1, tc1)) + (min(to1, tc1) - tl1)
                    body2_s1 = abs(tc2 - to2)
                    wicks2_s1 = (th2 - max(to2, tc2)) + (min(to2, tc2) - tl2)
                    
                    s1_bodies_larger = (body1_s1 > wicks1_s1) and (body2_s1 > wicks2_s1)
                    s1_break_lower = (tl2 < tl1)
                    
                    strat1_valid = s1_c1_red and s1_c2_red and s1_bodies_larger and s1_break_lower

                    # ==================== [الاستراتيجية الثانية - الشروط المرنة المحدثة] ====================
                    total_len1 = th1 - tl1
                    if total_len1 > 0:
                        body_sz1 = abs(to1 - tc1)
                        body_pct1 = (body_sz1 / total_len1) * 100
                        lower_pct1 = (l_wick_calc(to1, th1, tl1, tc1) / total_len1) * 100
                        upper_pct1 = (u_wick_calc(to1, th1, tl1, tc1) / total_len1) * 100
                        
                        s2_c1_valid = (45 <= body_pct1 <= 75) and (15 <= lower_pct1 <= 40) and (0 <= upper_pct1 <= 20)
                    else:
                        s2_c1_valid = False

                    total_len2 = th2 - tl2
                    if total_len2 > 0 and tc2 < to2:
                        body_sz2 = abs(to2 - tc2)
                        body_pct2 = (body_sz2 / total_len2) * 100
                        lower_pct2 = (l_wick_calc(to2, th2, tl2, tc2) / total_len2) * 100
                        upper_pct2 = (u_wick_calc(to2, th2, tl2, tc2) / total_len2) * 100

                        is_hammer = (10 <= body_pct2 <= 35) and (35 <= lower_pct2 <= 85) and (0 <= upper_pct2 <= 5)
                        is_filled_red_with_lower_wick = (body_pct2 >= 45) and (lower_pct2 >= 0) and (upper_pct2 <= 5)

                        s2_c2_valid = is_hammer or is_filled_red_with_lower_wick
                        s2_price_break = (tc2 < tl1)
                    else:
                        s2_c2_valid = False
                        s2_price_break = False

                    lw3 = l_wick_calc(to3, th3, tl3, tc3)
                    lw2 = l_wick_calc(to2, th2, tl2, tc2)
                    s2_c3_valid = (tc3 > to3) and (abs(to3 - tc2) <= (th2 - tl2) * 0.08) and (tc3 > th2) and (lw3 <= lw2 * 1.1)

                    strat2_valid = s2_c1_valid and s2_c2_valid and s2_price_break and s2_c3_valid

                    if strat1_valid or strat2_valid:
                        print(f"🎯 تطابق بـ {symbol.upper()} [{tf}] -> الاستراتيجية 1: {strat1_valid} | الاستراتيجية 2: {strat2_valid}", flush=True)

                    if strat1_valid:
                        key1 = f"{symbol}_{tf}_{c2['time']}_strategy1"
                        if key1 not in sent_alerts:
                            sent_alerts[key1] = True
                            msg1 = f"🚨 *تنبيه الاستراتيجية الأولى (الأصلية)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg1)

                    if strat2_valid:
                        key2 = f"{symbol}_{tf}_{c3['time']}_strategy2"
                        if key2 not in sent_alerts:
                            sent_alerts[key2] = True
                            msg2 = f"⭐ *تنبيه الاستراتيجية الثانية (المرنة)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                            send_telegram_message(msg2)

                    time.sleep(0.003)

            print(f"✅ اكتملت الدورة رقم {cycle} لكافة الفريمات", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
