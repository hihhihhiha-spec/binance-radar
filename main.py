import sys
import json
import time
import os
import threading
import requests
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- إعدادات تيليجرام ---
TELEGRAM_TOKEN = "8866274181:AAEU7Ofsem4EW87PNo1Uk_sNs0VSejcSmvI"
CHAT_ID = "6141474899"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=5)
        print(f"📤 [تيليجرام] تم الإرسال بنجاح (الكود: {response.status_code})", flush=True)
    except Exception as e:
        print(f"❌ Telegram Error: {e}", flush=True)

# --- سيرفر HTTP لضمان استمرار عمل Render ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar Ultimate Mode is Active")
    def log_message(self, format, *args): 
        pass

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🌐 HTTP Server running on port {port}", flush=True)
    sys.stdout.flush()
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

sent_alerts = {}

# --- جلب أعلى 200 عملة في الفيوتشرز حسب النسبة المئوية الصاعدة لـ 24 ساعة ---
def get_top_futures_symbols(limit=200):
    try:
        print("📡 جاري جلب وتحديث قائمة أعلى العملات صعوداً في الفيوتشرز لـ 24 ساعة...", flush=True)
        sys.stdout.flush()
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        movers = []
        for item in data:
            symbol = item['symbol']
            if symbol.endswith('USDT'):
                pct = float(item['priceChangePercent'])
                movers.append((symbol.lower(), pct))
        
        # ترتيب تنازلي حسب النسبة المئوية (الأعلى صعوداً في المقدمة) وبدون أي تكرار
        movers.sort(key=lambda x: x[1], reverse=True)
        
        seen = set()
        top_symbols = []
        for m in movers:
            if m[0] not in seen:
                seen.add(m[0])
                top_symbols.append(m[0])
            if len(top_symbols) >= limit:
                break
                
        print(f"🔥 تم تحديث واختيار أعلى {len(top_symbols)} عملة صعوداً بنجاح.", flush=True)
        sys.stdout.flush()
        return top_symbols
    except Exception as e:
        print(f"❌ خطأ في جلب العملات: {e}", flush=True)
        sys.stdout.flush()
        return []

# --- جلب الشموع التاريخية لكل عملة وفريم ---
def get_klines(symbol, interval, limit=15):
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            raw_data = response.json()
            candles = []
            for item in raw_data:
                candles.append({
                    'time': item[0],
                    'o': float(item[1]),
                    'h': float(item[2]),
                    'l': float(item[3]),
                    'c': float(item[4])
                })
            return candles
    except Exception as e:
        pass
    return []

# --- التحقق الهندسي الصارم ---
def evaluate_strategy(symbol, tf, candles):
    try:
        if len(candles) < 7:
            return
        
        c_prev2, c_prev1, c1, c2, c3, c4 = candles[-6], candles[-5], candles[-4], candles[-3], candles[-2], candles[-1]
        
        o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
        o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
        o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']
        o4, h4, l4, cl4 = c4['o'], c4['h'], c4['l'], c4['c']
        
        if not (c_prev2['h'] >= c_prev1['h'] and c_prev1['h'] >= h1):
            return

        if cl1 >= o1: return
        body1 = abs(o1 - cl1)
        upper_wick1 = h1 - max(o1, cl1)
        lower_wick1 = min(o1, cl1) - l1
        if not (body1 > upper_wick1 and body1 > lower_wick1): return
        if upper_wick1 > lower_wick1: return

        if cl2 >= o2: return
        body2 = abs(o2 - cl2)
        if not (body2 < body1 and l2 < l1 and cl2 < l1): return

        if cl3 <= o3: return
        if l3 < l2: return 
        
        middle_c1 = (h1 + l1) / 2
        if cl3 < middle_c1: return
        if cl3 > h1: return
        if h3 > h1: return

        middle_c3 = (h3 + l3) / 2
        if cl4 <= middle_c3: return

        alert_key = f"{symbol}_{tf}_{c4['time']}"
        if alert_key not in sent_alerts:
            sent_alerts[alert_key] = True
            msg = f"💎 *تنبيه بينانس (النموذج المطابق)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
            send_telegram_message(msg)
            print(f"🎯 تم اكتشاف النموذج وإرسال تنبيه للعملة: {symbol.upper()} على فريم {tf}", flush=True)
            sys.stdout.flush()

    except Exception as e:
        pass

# --- الحلقة الرئيسية مع التحديث التلقائي كل 5 ساعات ---
def main_loop():
    print("🚀 بدء تشغيل رادار الفيوتشرز الذكي...", flush=True)
    sys.stdout.flush()
    send_telegram_message("🟢 تم تشغيل رادار بينانس للفيوتشرز (أعلى 200 عملة صاعدة) بنجاح.")

    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '4h']
    
    symbols = []
    last_update_time = datetime.min

    while True:
        current_time = datetime.now()
        
        # تحديث قائمة أعلى 200 عملة تلقائياً كل 5 ساعات لتفادي الحظر تماماً
        if current_time - last_update_time >= timedelta(hours=5):
            print("🔄 [تحديث دوري] مرور 5 ساعات، جاري تحديث قائمة أعلى 200 عملة...", flush=True)
            sys.stdout.flush()
            symbols = get_top_futures_symbols(limit=200)
            last_update_time = current_time
            if not symbols:
                print("⚠️ فشل جلب العملات، إعادة المحاولة خلال دقيقة...", flush=True)
                sys.stdout.flush()
                time.sleep(60)
                continue

        print(f"\n🔄 --- بدء دورة فحص جديدة لـ {len(symbols)} عملة عبر {len(timeframes)} فريمات ---", flush=True)
        sys.stdout.flush()
        
        for symbol in symbols:
            for tf in timeframes:
                # طباعة واضحة وفورية لما يتم فحصه لترى الحركة في السجلات دون توقف
                print(f"🔍 [فحص مباشر] العملة: {symbol.upper()} | الفريم: {tf}", flush=True)
                sys.stdout.flush()
                
                candles = get_klines(symbol, tf, limit=15)
                if candles:
                    evaluate_strategy(symbol, tf, candles)
                
                time.sleep(0.15) # سرعة ممتازة ومريحة لعدم تجاوز حدود الخادم أو التعرض للحظر
                
        print("⏳ انتهاء الدورة الحالية. جاري البدء بالدورة التالية...", flush=True)
        sys.stdout.flush()
        time.sleep(10)

if __name__ == "__main__":
    main_loop()
