import ccxt
import time

# إعداد الاتصال بـ Binance Futures (الفيوتشرز)
exchange = ccxt.binance({'options': {'defaultType': 'future'}})

def check_pattern(symbol, timeframe):
    try:
        # جلب البيانات
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=3)
        if len(ohlcv) < 3: return None
        
        # الشمعة 1 (القديمة) والشمعة 2 (الأخيرة المكتملة)
        o1, h1, l1, c1 = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
        o2, h2, l2, c2 = ohlcv[1][1], ohlcv[1][2], ohlcv[1][3], ohlcv[1][4]

        # 1. شرط اللون: شمعتين حمراء (الإغلاق أقل من الافتتاح)
        if c1 < o1 and c2 < o2:
            
            # حساب الأجسام والذيول بدقة للفيوتشرز
            body2 = o2 - c2
            upper_wick2 = h2 - o2
            lower_wick2 = c2 - l2
            
            # 2. شرط كسر القاع: إغلاق الشمعة 2 تحت قاع الشمعة 1
            if c2 < l1:
                # 3. شرط الذيول: السفلي أطول من العلوي + الجسم أكبر من الذيول
                if lower_wick2 > upper_wick2 and body2 > (upper_wick2 + lower_wick2):
                    return True
    except:
        return None
    return False

# جلب جميع عملات الفيوتشرز تلقائياً لكي لا تفوت أي عملة
print("🔄 جلب قائمة عملات الفيوتشرز من بايننس...")
markets = exchange.fetch_markets()
symbols = [m['symbol'] for m in markets if m['active'] and m['quote'] == 'USDT']

print(f"🚀 تم العثور على {len(symbols)} عملة فيوتشرز. بدء الرادار المطور...")

while True:
    for tf in ['5m', '15m', '1h', '4h']:
        print(f"🔍 فحص إطار {tf} في سوق الفيوتشرز...")
        for sym in symbols:
            if check_pattern(sym, tf):
                print(f"🎯 فرصة فيوتشرز: {sym} ({tf}) | ذيل سفلي طويل + كسر قاع")
            # سرعة الفحص
        time.sleep(1)
    
    print("💤 دورة فحص انتهت. انتظار دقيقة...")
    time.sleep(60)
