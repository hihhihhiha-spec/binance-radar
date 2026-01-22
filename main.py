import ccxt
import time
from datetime import datetime

# إعداد الاتصال ببينانس فيوتشرز
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

# --- قائمة الـ 300 عملة مكتوبة يدوياً لسرعة التشغيل واستقراره ---
MY_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'LTC/USDT',
    'NEAR/USDT', 'MATIC/USDT', 'OP/USDT', 'ARB/USDT', 'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT',
    'TIA/USDT', 'SEI/USDT', 'SUI/USDT', 'APT/USDT', 'HBAR/USDT', 'ALGO/USDT', 'FIL/USDT', 'ICP/USDT', 'GRT/USDT', 'STX/USDT',
    'INJ/USDT', 'RNDR/USDT', 'FET/USDT', 'AGIX/USDT', 'OCEAN/USDT', 'TAO/USDT', 'THETA/USDT', 'EGLD/USDT', 'AAVE/USDT', 'UNI/USDT',
    'SUSHI/USDT', 'DYDX/USDT', 'CRV/USDT', 'MKR/USDT', 'LDO/USDT', 'PENDLE/USDT', 'ENS/USDT', 'ID/USDT', 'MAV/USDT', 'EDU/USDT',
    'GALA/USDT', 'ORDI/USDT', '1000SATS/USDT', 'BEAMX/USDT', 'PYTH/USDT', 'JUP/USDT', 'STRK/USDT', 'DYM/USDT', 'MANTA/USDT', 'ALT/USDT',
    'ZETA/USDT', 'PIXEL/USDT', 'RONIN/USDT', 'AXS/USDT', 'SAND/USDT', 'MANA/USDT', 'IMX/USDT', 'FLOW/USDT', 'CHZ/USDT', 'ENJ/USDT',
    'BEAM/USDT', 'YGG/USDT', 'ILV/USDT', 'MAGIC/USDT', 'RENDER/USDT', 'RUNE/USDT', 'KAS/USDT', 'TWT/USDT', 'GAS/USDT', 'NEO/USDT',
    'QTUM/USDT', 'VET/USDT', 'EGLD/USDT', 'CFX/USDT', 'KAVA/USDT', 'TOMO/USDT', 'IOTA/USDT', 'ZIL/USDT', 'ONT/USDT', 'BAT/USDT',
    # ملاحظة: القائمة طويلة جداً، عند تشغيل الكود لأول مرة سيقوم تلقائياً 
    # بإكمال أي نقص حتى يصل لـ 300 عملة لضمان شمولية السوق
]

# كود تكميلي لضمان وصول القائمة لـ 300 عملة (يُنفذ مرة واحدة عند التشغيل)
try:
    markets = exchange.load_markets()
    all_f = [s for s in markets if '/USDT' in s and ':' not in s]
    for s in all_f:
        if s not in MY_SYMBOLS and len(MY_SYMBOLS) < 300:
            MY_SYMBOLS.append(s)
except:
    pass

# الفريمات المطلوبة
TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']

def check_pattern(symbol, tf):
    try:
        # جلب آخر 3 شموع
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=3)
        if len(bars) < 3: return False
        
        # الشمعة المكتملة الأولى والثانية
        c1, c2 = bars[-3], bars[-2]
        o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
        o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]

        # شرط الشموع الحمراء
        if cl1 < o1 and cl2 < o2:
            body2 = abs(o2 - cl2)
            upper_tail2 = h2 - max(o2, cl2)
            lower_tail2 = min(o2, cl2) - l2
            
            # شرط الجسم أكبر من الذيول + كسر ذيل الشمعة السابقة
            if body2 > upper_tail2 and body2 > lower_tail2:
                if l2 < l1:
                    return True
        return False
    except:
        return False

print(f"✅ الرادار جاهز. العملات المستهدفة: {len(MY_SYMBOLS)}")
print(f"الفريمات: {TIMEFRAMES}")

while True:
    try:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n--- دورة فحص جديدة: {now} ---")
        
        total = len(MY_SYMBOLS)
        for index, symbol in enumerate(MY_SYMBOLS, 1):
            # عداد حي لترى أن الرادار يفحص الآن
            print(f"\r🔍 جاري فحص ({index}/{total}): {symbol}...", end="", flush=True)
            
            for tf in TIMEFRAMES:
                if check_pattern(symbol, tf):
                    print(f"\n🎯 [فرصة] {symbol} | فريم: {tf}")
            
            # تأخير بسيط لمنع الحظر
            time.sleep(0.02)
            
        print(f"\n✅ انتهى الفحص الشامل. سأعيد الكرة بعد دقيقتين...")
        time.sleep(120)
        
    except Exception as e:
        print(f"\n❌ خطأ تقني: {e}")
        time.sleep(60)
