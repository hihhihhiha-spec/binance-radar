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
        self.wfile.write(b"Safe Radar is Active")
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

# --- جلب أعلى 200 عملة في الفيوتشرز مع حماية تامة ضد الأخطاء ---
def get_top_futures_symbols(limit=200):
    try:
        print("📡 جاري جلب وتحديث قائمة أعلى العملات صعوداً في الفيوتشرز لـ 24 ساعة...", flush=True)
        sys.stdout.flush()
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠️ استجابة بينانس غير مرغوبة (الكود: {response.status_code})", flush=True)
            return []
            
        data = response.json()
        
        # التأكد من أن البيانات المدرج قادمة على شكل قائمة وليست خطأ نصي
        if not isinstance(data, list):
            print(f"⚠️ تحذير: البيانات المستلمة ليست قائمة صحيحة: {data}", flush=True)
            return []
        
        movers = []
        for item in data:
            if isinstance(item, dict) and 'symbol' in item and 'priceChangePercent' in item:
                symbol = item['symbol']
                if symbol.endswith('USDT'):
                    try:
                        pct = float(item['priceChangePercent'])
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
            if isinstance(raw_data, list):
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

# --- التحقق الصارم والمحدث للاستراتيجيتين ---
def evaluate_strategies(symbol, tf, candles):
    try:
        if len(candles) < 7:
            return
        
        c_prev2, c_prev1, c1, c2, c3, c4 = candles[-6], candles[-5], candles[-4], candles[-3], candles[-2], candles[-1]
        
        o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
        o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
        o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']
        o4, h4, l4, cl4 = c4['o'], c4['h'], c4['l'], c4['c']

        # ---------------------------------------------------------
        # الاستراتيجية الأولى
        # ---------------------------------------------------------
        try:
            if (c_prev2['h'] >= c_prev1['h'] and c_prev1['h'] >= h1):
                if cl1 < o1:
                    body1 = abs(o1 - cl1)
                    upper_wick1 = h1 - max(o1, cl1)
                    lower_wick1 = min(o1, cl1) - l1
                    if body1 > upper_wick1 and body1 > lower_wick1 and upper_wick1 <= lower_wick1:
                        if cl2 < o2:
                            body2 = abs(o2 - cl2)
                            if body2 < body1 and l2 < l1 and cl2 < l1:
                                if cl3 > o3 and l3 >= l2:
                                    middle_c1 = (h1 + l1) / 2
                                    if middle_c1 <= cl3 <= h1 and h3 <= h1:
                                        middle_c3 = (h3 + l3) / 2
                                        if cl4 > middle_c3:
                                            alert_key = f"{symbol}_{tf}_{c4['time']}_strat1"
                                            if alert_key not in sent_alerts:
                                                sent_alerts[alert_key] = True
                                                msg = f"💎 *تنبيه بينانس (الاستراتيجية الأولى)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                                                send_telegram_message(msg)
                                                print(f"🎯 تم اكتشاف نموذج الاستراتيجية 1 للعملة: {symbol.upper()} على فريم {tf}", flush=True)
                                                sys.stdout.flush()
                                                return
        except Exception:
            pass

        # ---------------------------------------------------------
        # الاستراتيجية الثانية
        # ---------------------------------------------------------
        try:
            if cl1 < o1:
                body1 = abs(o1 - cl1)
                u_wick1 = h1 - max(o1, cl1)
                l_wick1 = min(o1, cl1) - l1
                
                if body1 > u_wick1 and body1 > l_wick1:
                    if cl2 < o2:
                        body2 = abs(o2 - cl2)
                        if body2 > body1 and l2 < l1:
                            if cl3 > o3:
                                middle_c3 = (h3 + l3) / 2
                                if (l3 >= l1 and h3 <= h1) and (l4 >= l1 and h4 <= h1) and (cl4 > middle_c3):
                                    alert_key = f"{symbol}_{tf}_{c4['time']}_strat2"
                                    if alert_key not in sent_alerts:
                                        sent_alerts[alert_key] = True
                                        msg = f"🚀 *تنبيه بينانس (الاستراتيجية الثانية)*\n🔹 العملة: `{symbol.upper()}`\n⏱️ الفريم: `{tf}`"
                                        send_telegram_message(msg)
                                        print(f"🎯 تم اكتشاف نموذج الاستراتيجية 2 للعملة: {symbol.upper()} على فريم {tf}", flush=True)
                                        sys.stdout.flush()
        except Exception:
            pass

    except Exception as e:
        pass

# --- الحلقة الرئيسية مع التحديث التلقائي كل 5 ساعات ---
def main_loop():
    print("🚀 بدء تشغيل رادار الفيوتشرز الذكي (النسخة الآمنة والمحدثة)...", flush=True)
    sys.stdout.flush()
    send_telegram_message("🟢 تم تشغيل رادار بينانس للفيوتشرز (نسخة معالجة أخطاء بينانس) بنجاح.")

    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '4h']
    
    symbols = []
    last_update_time = datetime.min

    while True:
        current_time = datetime.now()
        
        # تحديث قائمة أعلى 200 عملة تلقائياً كل 5 ساعات أو إذا كانت القائمة فارغة
        if not symbols or (current_time - last_update_time >= timedelta(hours=5)):
            print("🔄 جاري تحديث قائمة أعلى 200 عملة...", flush=True)
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
                candles = get_klines(symbol, tf, limit=15)
                if candles:
                    evaluate_strategies(symbol, tf, candles)
                
                time.sleep(0.15)
                
        print("⏳ انتهاء الدورة الحالية. جاري البدء بالدورة التالية...", flush=True)
        sys.stdout.flush()
        time.sleep(10)

if __name__ == "__main__":
    main_loop()
