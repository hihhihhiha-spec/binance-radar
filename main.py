import ccxt
import time

# الاتصال المباشر بمحرك الفيوتشرز في بايننس
exchange = ccxt.binance({'options': {'defaultType': 'future'}})

def check_pattern(symbol, timeframe):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=3)
        if len(ohlcv) < 3: return None
        
        # الشمعة 1 (القبل أخيرة) والشمعة 2 (الأخيرة المكتملة)
        o1, h1, l1, c1 = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
        o2, h2, l2, c2 = ohlcv[1][1], ohlcv[1][2], ohlcv[1][3], ohlcv[1][4]

        # 1. شرط اللون الصارم: شمعتان حمراوان متتاليتان
        if c1 < o1 and c2 < o2:
            
            # حسابات الذيول والجسم للشمعة الثانية
            body2 = o2 - c2
            upper_wick2 = h2 - o2
            lower_wick2 = c2 - l2
            
            # 2. شرط كسر القاع: إغلاق الثانية تحت أدنى سعر (ذيل) الأولى
            if c2 < l1:
                # 3. شرط الذيول: السفلي أطول من العلوي + الجسم قوي (ليس دوجي)
                if lower_wick2 > upper_wick2 and body2 > (upper_wick2 + lower_wick2):
                    return True
    except:
        return None
    return False

# جلب عملات الفيوتشرز النشطة فقط
print("📡 جلب قائمة عملات Futures USDT...")
markets = exchange.fetch_markets()
symbols = [m['symbol'] for m in markets if m['active'] and m['linear'] and m['quote'] == 'USDT']
print(f"✅ تم العثور على {len(symbols)} عملة. بدء الفحص...")

while True:
    for tf in ['5m', '15m', '1h', '4h']:
        print(f"🔍 فحص إطار {tf}...")
        for sym in symbols:
            if check_pattern(sym, tf):
                print(f"🎯 صيد فيوتشرز: {sym} ({tf}) | شمعتين حمراء + ذيل سفلي طويل")
            time.sleep(0.1) # سرعة الفحص لمنع ضغط السيرفر
    
    print("💤 انتهاء الدورة. استراحة دقيقة...")
    time.sleep(60)
