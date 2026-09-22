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
        self.wfile.write(b"Diagnostic Strategy 3 Radar is Active")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

sent_alerts = {}
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_top_futures_symbols(limit=200):
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
            return [m[0] for m in movers[:limit]]
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
    print("🟢 [تشخيص دقيق] بدأ رادار الاستراتيجية الثالثة للتشخيص المكشوف...", flush=True)
    send_telegram_message("🟢 بدأ تشغيل رادار التشخيص الفني للوقوف على سبب عدم ظهور التنبيهات.")

    timeframes = ['1m', '5m', '15m', '1h', '4h']
    symbols = []
    last_update_time = datetime.min
    cycle = 1

    while True:
        try:
            current_time = datetime.now()
            if not symbols or (current_time - last_update_time >= timedelta(hours=3)):
                symbols = get_top_futures_symbols(limit=200)
                last_update_time = current_time
                if not symbols:
                    time.sleep(30)
                    continue

            print(f"\n🔄 [دورة تشخيص رقم {cycle}] جاري فحص {len(symbols)} عملة...", flush=True)

            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    candles = get_klines(symbol, tf, limit=10)
                    if not candles or len(candles) < 4:
                        continue
                    
                    # نأخذ آخر 3 شموع مكتملة تماماً (نتجنب الشمعة الحالية غير المغلقة [-1] ونأخذ [-4, -3, -2])
                    c1, c2, c3 = candles[-4], candles[-3], candles[-2]
                    o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
                    o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
                    o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']

                    # فحص الشمعة الأولى
                    if cl1 >= o1:
                        continue
                    body1, u_wick1, l_wick1 = get_wick_body(o1, h1, l1, cl1)
                    if not (body1 > l_wick1 and l_wick1 > u_wick1):
                        continue

                    # فحص الشمعة الثانية (المطرقة الحمراء)
                    body2, u_wick2, l_wick2 = get_wick_body(o2, h2, l2, cl2)
                    
                    # إذا وصلت العملة إلى هنا، فهذا يعني أن الشمعة الأولى والثانية انطبقت تماماً!
                    # سنقوم بطباعة رسالة واضحة جداً في السجلات لترى العملة والفريم والأسعار
                    print(🎯 [ايجاد محتمل] العملة {symbol.upper()} على فريم {tf} اجتازت الشمعة 1 و 2 بنجاح! فحص الشمعة 3..., flush=True)
                    print(   -> C1: O={o1}, H={h1}, L={l1}, C={cl1}, LW={l_wick1}, UW={u_wick1}, Body={body1}, flush=True)
                    print(   -> C2: O={o2}, H={h2}, L={l2}, C={cl2}, LW={l_wick2}, UW={u_wick2}, Body={body2}, flush=True)

                    # فحص الشمعة الثالثة
                    if cl3 <= o3:
                        print(❌ [فشل الشمعة 3] الشمعة الثالثة ليست صاعدة (C={cl3} <= O={o3}), flush=True)
                        continue

                    trailing_condition = (l3 >= l1 and h3 <= h1) and (l3 >= l2 and cl3 > h2)
                    if not trailing_condition:
                        print(❌ [فشل الشروط] الشمعة الثالثة خالفت شرط النطاق أو الاختراق., flush=True)
                        continue

                    # تحقق كامل
                    key = f"{symbol}_{tf}_{c3['time']}_diag_s3"
                    if key not in sent_alerts:
                        sent_alerts[key] = True
                        msg = f"⭐ *تنبيه تشخيصي ناجح*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                        send_telegram_message(msg)
                        print(f"🚨 [تم الارسال بنجاح!] {symbol.upper()} - {tf}", flush=True)

                    time.sleep(0.01)

            print(f"✅ اكتملت دورة التشخيص رقم {cycle}", flush=True)
            cycle += 1
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ خطأ: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
