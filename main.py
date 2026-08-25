import os
import time
import requests
import ccxt
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# ================= إعدادات تيليجرام =================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7941785535:AAEqT4kF2-1r7J4jS7xV9Z8L1mN3p5Q7r2s")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5119045763")

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending telegram message: {e}")

# ================= خادم الحفاظ على النشاط (Dummy Server) =================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar is Active and Running!")
    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    print(f"Dummy Server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ================= منطق الرادار والاتصال بمنصة بينانس =================
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

TIMEFRAMES = ['15m', '1h', '4h', '1d']
checked_signals = set()

def check_three_candle_pattern(ohlcv):
    """
    التحقق من نمط الشموع:
    1. شمعة [i-2]: حمراء.
    2. شمعة [i-1]: حمراء، طويلة، ولها ذيل سفلي طويل جداً (رفض سعري).
    3. شمعة [i]: خضراء، وجسمها بالكامل يقع داخل جسم الشمعة الحمراء الثانية (محتواة داخله).
    """
    if len(ohlcv) < 3:
        return False
    
    c1, c2, c3 = ohlcv[-3], ohlcv[-2], ohlcv[-1]
    
    # 1. الشمعة الأولى [i-2] حمراء
    open1, close1 = c1[1], c1[4]
    is_red_1 = close1 < open1
    
    # 2. الشمعة الثانية [i-1] (الرئيسية ذات الذيل الطويل)
    open2, high2, low2, close2 = c2[1], c2[2], c2[3], c2[4]
    is_red_2 = close2 < open2
    body2 = abs(close2 - open2)
    lower_wick2 = min(open2, close2) - low2
    
    # شروط الشمعة الثانية: حمراء، جسم واضح، ذيل سفلي طويل جداً (أكبر من الجسم بضعفين على الأقل)
    cond_candle_2 = (is_red_2 and body2 > 0 and lower_wick2 >= (body2 * 2))
    
    # 3. الشمعة الثالثة [i] (الخضراء الداخلية)
    open3, close3 = c3[1], c3[4]
    is_green_3 = close3 > open3
    
    # حدود جسم الشمعة الثانية (الأعلى والأسفل للجسم فقط)
    body2_top = max(open2, close2)
    body2_bottom = min(open2, close2)
    
    # حدود جسم الشمعة الثالثة
    body3_top = max(open3, close3)
    body3_bottom = min(open3, close3)
    
    # شرط أن تكون الشمعة الخضراء بالكامل داخل جسم الشمعة الحمراء الثانية
    is_inside_body = (is_green_3 and body3_top <= body2_top and body3_bottom >= body2_bottom)
    
    # التحقق من اكتمال النموذج
    if is_red_1 and cond_candle_2 and is_inside_body:
        return True
        
    return False

def scan_market():
    print("Fetching markets from Binance...")
    try:
        exchange.load_markets()
        symbols = [symbol for symbol in exchange.symbols if '/USDT:USDT' in symbol or symbol.endswith('/USDT')]
    except Exception as e:
        print(f"Error loading markets: {e}")
        return

    print(f"Monitoring {len(symbols)} symbols across timeframes: {TIMEFRAMES}")
    send_telegram_message("🚀 *تم تحديث الرادار بنجاح: الشمعة الخضراء أصبحت مشروطة بأن تكون داخل جسم الشمعة الحمراء بدقة!*")

    while True:
        for symbol in symbols:
            for tf in TIMEFRAMES:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
                    if not ohlcv or len(ohlcv) < 3:
                        continue
                    
                    last_candle_time = ohlcv[-1][0]
                    signal_id = f"{symbol}_{tf}_{last_candle_time}"
                    
                    if signal_id in checked_signals:
                        continue

                    if check_three_candle_pattern(ohlcv):
                        checked_signals.add(signal_id)
                        
                        if len(checked_signals) > 2000:
                            checked_signals.clear()

                        msg = (
                            f"🚨 *فرصة مطابقة للنموذج بدقة!*\n\n"
                            f"🪙 العملة: `{symbol}`\n"
                            f"⏱ الفريم: `{tf}`\n"
                            f"📊 الاستراتيجية: شمعتان حمراوان (الثانية بذيل طويل) + خضراء داخل جسم الثانية\n"
                            f"⏰ الوقت: تفعيل إشارة الشمعة الأخيرة."
                        )
                        send_telegram_message(msg)
                        print(f"Signal found and sent: {symbol} on {tf}")

                    time.sleep(exchange.rateLimit / 1000)
                except Exception as e:
                    continue
        
        time.sleep(30)

if __name__ == "__main__":
    scan_market()
