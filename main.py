import ccxt
import time
import sys
import pandas as pd
from datetime import datetime

def play_beep_alert():
    """توليد صوت Beep متكرر بالتزامن مع طباعة الشاشة"""
    print("\a", end="", flush=True)  # صوت System Beep
    try:
        import winsound
        # أصوات Beep متكررة بنغمة مرتفعة (التردد: 1000 هرتز، المدة: 500 مللي ثانية)
        for _ in range(5):
            winsound.Beep(1000, 500)
            time.sleep(0.1)
    except ImportError:
        # لنظام ماك أو لينكس
        for _ in range(5):
            print("\a", end="", flush=True)
            time.sleep(0.3)

def check_pattern(df):
    """التحقق من شرط الشموع"""
    if len(df) < 3:
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

def run_radar():
    exchange = ccxt.binance({
        'enableRateLimit': True,  # حماية الـ IP تلقائياً
        'options': {'defaultType': 'spot'}
    })

    timeframes = ['1m', '3m', '5m', '1h']
    print("🚀 تم تشغيل الرادار بصوت Beep... جاري الفحص...")

    while True:
        try:
            markets = exchange.load_markets()
            symbols = [s for s in markets if s.endswith('/USDT') and markets[s]['active']]

            for symbol in symbols:
                for tf in timeframes:
                    try:
                        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
                        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

                        if check_pattern(df):
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print(f"\n🚨 [تنبيه رصد] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}")
                            
                            # تشغيل صوت الـ Beep
                            play_beep_alert()
                            
                            input("⚠️ اضغط Enter لمتابعة الفحص لعملات أخرى...")

                    except ccxt.RateLimitExceeded as e:
                        print(f"🛑 [تنبيه IP]: تم كسر معدل الطلبات، جاري الانتظار 10 ثوانٍ... التفاصيل: {e}")
                        time.sleep(10)
                    except ccxt.NetworkError as e:
                        print(f"🌐 [خطأ شبكة]: تعذر الاتصال بـ Binance: {e}")
                    except Exception as e:
                        print(f"⚠️ [خطأ في الزوج {symbol} فريم {tf}]: {e}")
                    
                    time.sleep(0.1) # مهلة حماية لتجنب حظر الـ IP

        except Exception as e:
            print(f"❌ [خطأ عام في السكربت]: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_radar()
