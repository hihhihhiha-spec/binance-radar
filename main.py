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
        print(f"📤 [تيليجرام] تم الإرسال بنجاح (الكود: {response.status_code})", flush=True)
    except Exception as e:
        print(f"❌ Telegram Error: {e}", flush=True)

# --- سيرفر HTTP أساسي لـ Render ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar is Running")
    def log_message(self, format, *args):
        pass

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"🌐 [سيرفر Render] يعمل بنجاح على البورت {port}", flush=True)
        sys.stdout.flush()
        server.serve_forever()
    except Exception as e:
        print(f"❌ خطأ في تشغيل السيرفر: {e}", flush=True)
        sys.stdout.flush()

threading.Thread(target=run_http_server, daemon=True).start()

sent_alerts = {}

# هيدر متصفح حقيقي لتجنب أي حظر
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# --- جلب أعلى العملات من واجهة Spot الآمنة ضد الحظر ---
def get_top_futures_symbols(limit=200):
    try:
        print("📡 [بينانس] جاري جلب قائمة العملات الصاعدة من خادم السبوت البديل...", flush=True)
        sys.stdout.flush()
        # استخدام واجهة Spot العامة لتجنب حظر IP على الفيوتشرز
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠️ خطأ في الاستجابة (الكود: {response.status_code})", flush=True)
            sys.stdout.flush()
            return []
            
        data = response.json()
        if not isinstance(data, list):
            print(f"⚠️ البيانات المستلمة ليست قائمة صحيحة", flush=True)
            sys.stdout.flush()
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
                
        print(f"🔥 [نجاح] تم اختيار أعلى {len(top_symbols)} عملة بنجاح.", flush=True)
        sys.stdout.flush()
        return top_symbols
    except Exception as e:
        print(f"❌ خطأ في جلب العملات: {e}", flush=True)
        sys.stdout.flush()
        return []

# --- جلب الشموع (من الفيوتشرز مباشرة للفحص) ---
def get_klines(symbol, interval, limit=15):
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
        response = requests.get(url, headers=HEADERS, timeout=5)
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

# --- التحقق من الاستراتيجيتين ---
def evaluate_strategies(symbol, tf, candles):
    try:
        if len(candles) < 7:
            return
        
        c_prev2, c_prev1, c1, c2, c3, c4 = candles[-6], candles[-5], candles[-4], candles[-3], candles[-2], candles[-1]
        
        o1, h1, l1, cl1 = c1['o'], c1['h'], c1['l'], c1['c']
        o2, h2, l2, cl2 = c2['o'], c2['h'], c2['l'], c2['c']
        o3, h3, l3, cl3 = c3['o'], c3['h'], c3['l'], c3['c']
        o4, h4, l4, cl4 = c4['o'], c4['h'], c4['l'], c4['c']

        # الاستراتيجية الأولى
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
                                                print(f"🎯 [هدف] نموذج الاستراتيجية 1 للعملة: {symbol.upper()} على فريم {tf}", flush=True)
                                                sys.stdout.flush()
                                                return
        except Exception:
            pass

        # الاستراتيجية الثانية
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
                                        print(f"🎯 [هدف] نموذج الاستراتيجية 2 للعملة: {symbol.upper()} على فريم {tf}", flush=True)
                                        sys.stdout.flush()
        except Exception:
            pass

    except Exception as e:
        pass

# --- الدورة الرئيسية ---
def main_loop():
    print("🚀 [بدء التشغيل] تم تشغيل النظام الرئيسي للرادار...", flush=True)
    sys.stdout.flush()
    send_telegram_message("🟢 تم تشغيل رادار بينانس بنجاح وبدء المراقبة الفورية.")

    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '4h']
    symbols = []
    last_update_time = datetime.min

    while True:
        current_time = datetime.now()
        
        if not symbols or (current_time - last_update_time >= timedelta(hours=5)):
            print("🔄 [تحديث] جلب قائمة العملات الصاعدة...", flush=True)
            sys.stdout.flush()
            symbols = get_top_futures_symbols(limit=200)
            last_update_time = current_time
            if not symbols:
                print("⚠️ [تنبيه] فشل جلب العملات، إعادة المحاولة خلال دقيقة...", flush=True)
                sys.stdout.flush()
                time.sleep(60)
                continue

        print(f"\n🔄 [دورة فحص جديدة] فحص {len(symbols)} عملة عبر {len(timeframes)} فريمات...", flush=True)
        sys.stdout.flush()
        
        for symbol in symbols:
            for tf in timeframes:
                candles = get_klines(symbol, tf, limit=15)
                if candles:
                    evaluate_strategies(symbol, tf, candles)
                
                time.sleep(0.2)
                
        print("⏳ [استراحة] انتهاء الدورة الحالية، الانتقال للدورة التالية...", flush=True)
        sys.stdout.flush()
        time.sleep(10)

if __name__ == "__main__":
    main_loop()
