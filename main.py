import sys
import json
import time
import os
import threading
import requests
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- تفعيل الطباعة الفورية بدون تخزين مؤقت ---
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# --- إعدادات تيليجرام ---
TELEGRAM_TOKEN = "8866274181:AAEU7Ofsem4EW87PNo1Uk_sNs0VSejcSmvI"
CHAT_ID = "6141474899"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=5)
        print(f"📤 [تيليجرام] تم الإرسال (الكود: {response.status_code})", flush=True)
    except Exception as e:
        print(f"❌ Telegram Error: {e}", flush=True)

# --- سيرفر HTTP أساسي لـ Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Debug Tracing Strategy 3 Radar is Active")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 [HTTP Server] يعمل على البورت {port}", flush=True)
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

sent_alerts = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Chrome/122.0.0.0 Safari/537.36)",
    "Accept": "application/json"
}

# --- جلب أعلى 200 عملة صاعدة من بايبت ---
def get_top_futures_symbols(limit=200):
    try:
        print("📡 [بايبت] جاري جلب قائمة أعلى 200 عملة (Linear Futures)...", flush=True)
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("retCode") == 0:
                data = result.get("result", {}).get("list", [])
                movers = []
                for item in data:
                    symbol = item.get('symbol', '')
                    if symbol.endswith('USDT'):
                        try:
                            pct = float(item.get('price24hPcnt', 0)) * 100
                            movers.append((symbol.lower(), pct))
                        except ValueError:
                            continue
                movers.sort(key=lambda x: x[1], reverse=True)
                seen = set()
                top_symbols = []
                for m in movers:
                    if m[0] not in seen:
                        seen.add(m[0])
                        top_symbols.append(m[0])
                    if len(top_symbols) >= limit:
                        break
                print(f"🔥 [نجاح] تم جلب واعتماد {len(top_symbols)} عملة للفحص.", flush=True)
                return top_symbols
    except Exception as e:
        print(f"❌ خطأ جلب العملات: {e}", flush=True)
    return []

BYBIT_INTERVALS = {
    '1m': '1',
    '3m': '3',
    '5m': '5',
    '15m': '15',
    '30m': '30',
    '1h': '60',
    '4h': '240'
}

def get_klines(symbol, interval, limit=15):
    try:
        bybit_tf = BYBIT_INTERVALS.get(interval, '60')
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol.upper()}&interval={bybit_tf}&limit={limit}"
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("retCode") == 0:
                raw_data = res_json.get("result", {}).get("list", [])
                if isinstance(raw_data, list):
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
    except Exception as e:
        print(f"⚠️ خطأ جلب شموع {symbol.upper()} على الفريم {interval}: {e}", flush=True)
    return []

def get_wick_body(o, h, l, c):
    body = abs(o - c)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    return body, upper_wick, lower_wick

def main():
    print("🟢 [بدء التشغيل] رادار التتبع التصحيحي يعمل الآن...", flush=True)
    send_telegram_message("🟢 تم تشغيل رادار التتبع لمعرفة أين تفحص الشروط بدقة.")

    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '4h']
    symbols = []
    last_update_time = datetime.min
    cycle_counter = 1

    while True:
        try:
            current_time = datetime.now()
            
            # تحديث قائمة العملات كل 3 ساعات
            if not symbols or (current_time - last_update_time >= timedelta(hours=3)):
                symbols = get_top_futures_symbols(limit=200)
                last_update_time = current_time
                if not symbols:
                    print("⚠️ قائمة العملات فارغة، إعادة المحاولة بعد 30 ثانية...", flush=True)
                    time.sleep(30)
                    continue

            print(f"\n🔄 [بدء الدورة رقم {cycle_counter}] فحص إجمالي {len(symbols)} عملة...", flush=True)
            
            for idx, symbol in enumerate(symbols):
                for tf in timeframes:
                    # سطر التتبع المباشر لتحديد أين يعمل الرادار لحظياً
                    print(f"🔍 [دورة {idx+1}/{len(symbols)}] فحص العملة: {symbol.upper()} | الفريم: {tf}", flush=True)
                    
                    candles = get_klines(symbol, tf, limit=15)
                    if not candles or len(candles) < 7:
                        continue # تخطي إذا البيانات غير كافية
                        
                    c1, c2, c3 = candles[-4], candles[-3], candles[-2]
                    o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
                    o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
                    o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']

                    # --- تتبع الشروط خطوة بخطوة لمعرفة أين تسقط العملة ---
                    
                    # 1. شرط الشمعة الأولى
                    if cl1 >= o1:
                        continue # سقطت لأنها ليست هابطة
                        
                    body1, u_wick1, l_wick1 = get_wick_body(o1, h1, l1, cl1)
                    if not (body1 > l_wick1 and l_wick1 > u_wick1):
                        continue # سقطت عند تفاصيل ديول الشمعة الأولى
                        
                    # 2. شرط الشمعة الثانية (المطرقة الحمراء الصارمة)
                    body2, u_wick2, l_wick2 = get_wick_body(o2, h2, l2, cl2)
                    
                    # طباعة تتبع إذا اجتازت الشمعة الأولى واقتربت من التحقق
                    # (هذا السطر سيطبع في السجلات إذا وجدت عملة تطابق الشمعة الأولى والثانية لتكتشف هل المشكلة في الشمعة الثالثة)
                    if cl2 < o2 and l2 < l1:
                        print(f"💡 [تتبع متقدم] {symbol.upper()} على {tf} اجتازت الشمعة الأولى والثانية جزئياً. فحص الشمعة الثالثة...", flush=True)

                    if not (cl2 < o2 and u_wick2 == 0 and l2 < l1 and 
                            cl2 < (l1 - l_wick1) and 
                            (body2 >= l_wick2 or l_wick2 >= body2)):
                        continue # سقطت عند شروط الشمعة الثانية (المطرقة الحمراء أو كسر الذيل)

                    # 3. شرط الشمعة الثالثة (التتبع والصعود)
                    if cl3 <= o3:
                        print(f"⚠️ [تتبع] {symbol.upper()} على {tf} وصلت للشمعة الثالثة لكنها ليست صاعدة.", flush=True)
                        continue

                    trailing_condition = (l3 >= l1 and h3 <= h1) and (l3 >= l2 and cl3 > h2)
                    if not trailing_condition:
                        print(f"⚠️ [تتبع] {symbol.upper()} على {tf} وصلت للشمعة الثالثة ولم تحقق شرط التتبع أو الاختراق.", flush=True)
                        continue

                    # إذا وصلت إلى هنا، فهذا يعني أن النموذج قد تحقق بنجاح 100%!
                    key = f"{symbol}_{tf}_{c3['time']}_debug_s3"
                    if key not in sent_alerts:
                        sent_alerts[key] = True
                        msg = f"⭐ *تنبيه (الاستراتيجية الثالثة - مطابقة كاملة)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                        send_telegram_message(msg)
                        print(f"🎯 [هدف محقق بنجاح!] تم إرسال تنبيه لـ {symbol.upper()} على فريم {tf}", flush=True)

                    time.sleep(0.02)

            print(f"\n✅ [اكتملت الدورة رقم {cycle_counter} تماماً]\n" + "="*50, flush=True)
            cycle_counter += 1
            time.sleep(5)

        except Exception as e:
            print(f"❌ [خطأ رئيسي في السطر أو الحلقة]: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
