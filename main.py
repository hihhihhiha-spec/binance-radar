import ccxt
import time
from datetime import datetime

# إعداد الاتصال ببينانس فيوتشرز
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

# قائمة الـ 300 عملة (مثبتة لضمان الاستقرار)
MY_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'LTC/USDT',
    'NEAR/USDT', 'MATIC/USDT', 'OP/USDT', 'ARB/USDT', 'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT',
    'TIA/USDT', 'SEI/USDT', 'SUI/USDT', 'APT/USDT', 'HBAR/USDT', 'ALGO/USDT', 'FIL/USDT', 'ICP/USDT', 'GRT/USDT', 'STX/USDT'
    # سيتم تكملة الباقي تلقائياً في الذاكرة ليصل لـ 300 عند التشغيل
]

try:
    m = exchange.load_markets()
    all_f = [s for s in m if '/USDT' in s and ':' not in s]
    for s in all_f:
        if s not in MY_SYMBOLS and len(MY_SYMBOLS) < 300:
            MY_SYMBOLS.append(s)
except:
    pass

TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']

def check_pattern(symbol, tf):
    try:
        # سحب 5 شموع لضمان دقة البيانات كما طلبت
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
        if len(bars) < 5: return False
        
        # نركز على آخر شمعتين أغلقت تماماً
        # c1 هي الشمعة السابقة، c2 هي الشمعة الأخيرة المكتملة
        c1 = bars[-3] 
        c2 = bars[-2] 

        o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
        o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]

        # 1. شرط الشموع الحمراء (الإغلاق تحت الافتتاح)
        if cl1 < o1 and cl2 < o2:
            
            # حساب الأجسام والذيول للشمعتين
            body1 = abs(o1 - cl1)
            u_tail1 = h1 - max(o1, cl1)
            l_tail1 = min(o1, cl1) - l1

            body2 = abs(o2 - cl2)
            u_tail2 = h2 - max(o2, cl2)
            l_tail2 = min(o2, cl2) - l2

            # 2. شرط الجسم أكبر من الذيول في الشمعتين
            if body1 > (u_tail1 + l_tail1) and body2 > (u_tail2 + l_tail2):
                
                # 3. شرط الذيل السفلي أكبر من العلوي في الشمعتين
                if l_tail1 > u_tail1 and l_tail2 > u_tail2:
                    
                    # 4. شرط الكسر والإغلاق: الشمعة الثانية أغلقت تحت أدنى سعر (Low) للشمعة الأولى
                    if cl2 < l1:
                        return True
        return False
    except:
        return False

print(f"🚀 الرادار المطور يعمل الآن.. الفحص يعتمد على 5 شموع وإغلاق مؤكد.")

while True:
    try:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n--- دورة فحص جديدة: {now} ---")
        
        total = len(MY_SYMBOLS)
        for index, symbol in enumerate(MY_SYMBOLS, 1):
            # رسالة الفحص المستمرة للتأكد من عمل الرادار
            print(f"[{now}] ({index}/{total}) فحص مستمر: {symbol}")
            
            for tf in TIMEFRAMES:
                if check_pattern(symbol, tf):
                    print(f"🎯 فرصة ذهبية (كسر وإغلاق): {symbol} | فريم: {tf}")
            
            time.sleep(0.05) 
            
        print(f"✅ انتهى الفحص الشامل. انتظار دقيقتين...")
        time.sleep(120)
    except Exception as e:
        print(f"❌ خطأ: {e}")
        time.sleep(60)
