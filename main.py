import ccxt
import time
import sys
import pandas as pd
from datetime import datetime

def play_beep_alert():
    """توليد صوت Beep تنبيهي"""
    try:
        import winsound
        for _ in range(5):
            winsound.Beep(1000, 400)
            time.sleep(0.1)
    except Exception:
        for _ in range(5):
            print("\a", end="", flush=True)
            time.sleep(0.2)

def check_pattern(df):
    """فحص شرط الشموع"""
    try:
        if df is None or len(df) < 3:
            return False

        prev_candle = df.iloc[-3]
        red_candle = df.iloc[-2]
        green_candle = df.iloc[-1]

        # 1. شمعة حمراء أكبر من التي قبلها وتغلق تحت ذيلها
        is_red = red_candle['close'] < red_candle['open']
        red_body = abs(red_candle['close'] - red_candle['open'])
        prev_body = abs(prev_candle['close'] - prev_candle['open'])
        
        is_bigger = red_body > prev_body
        breaks_lower_tail = red_candle['close'] < prev_candle['low']

        if not (is_red and is_bigger and breaks_lower_tail):
            return False

        # 2. شمعة خضراء تالية تغلق في نصف الشمعة الحمراء على الأقل
        is_green = green_candle['close'] > green_candle['open']
        red_midpoint = red_candle['open'] - (red_body / 2)
        closes_at_half = green_candle['close'] >= red_midpoint

        return is_green and closes_at_half
    except Exception as e:
        # تفادي الأخطاء في حسابات الحجم والأسعار
        return False

def run_radar():
    exchange = ccxt.binance({
        'enableRateLimit': True, # أقصى حماية لـ IP
        'timeout': 15000,        # 15 ثانية حد أقصى للانتظار
        'options': {'defaultType': 'spot'}
    })

    timeframes = ['1m', '3m', '5m', '1h']
    print("🚀 بدء الرادار بحماية شاملة ضد السقوط... جاري الفحص...")

    while True:
        try:
            # تحميل الأسواق مع معالجة الاستثناءات
            try:
                markets = exchange.load_markets()
                symbols = [s for s in markets if s.endswith('/USDT') and markets[s].get('active', True)]
            except Exception as e:
                print(f"⚠️ [خطأ في تحميل أسواق Binance]: {e} | إعادة المحاولة بعد 5 ثوانٍ...")
                time.sleep(5)
                continue

            for symbol in symbols:
                for tf in timeframes:
                    try:
                        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
                        if not ohlcv or len(ohlcv) < 3:
                            continue

                        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

                        if check_pattern(df):
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print(f"\n🚨 [تم الرصد بنجاح] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}")
                            
                            play_beep_alert()
                            input("⚠️ اضغط Enter لمتابعة البحث...")

                    except ccxt.RateLimitExceeded as e:
                        print(f"🛑 [تجاوز معدل الطلبات IP]: {e} | جاري الانتظار 10 ثوانٍ...")
                        time.sleep(10)
                    except ccxt.NetworkError as e:
                        print(f"🌐 [خطأ اتصال بشبكة الإنترنت]: {e}")
                        time.sleep(2)
                    except Exception as e:
                        print(f"⚠️ [خطأ في الزوج {symbol} فريم {tf}]: {e}")
                    
                    # مهلة بين كل طلب لحماية IP
                    time.sleep(0.12)

        except KeyboardInterrupt:
            print("\n🛑 تم إيقاف الرادار يدوياً.")
            break
        except Exception as e:
            print(f"❌ [خطأ عام غير متوقع]: {e} | جاري استئناف العمل خلال 3 ثوانٍ...")
            time.sleep(3)

if __name__ == "__main__":
    run_radar()
