import ccxt, time, threading, os
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "Radar is Live and Hunting"

def radar_logic():
    # الاتصال بفيوتشرز بايننس لضمان دقة البيانات [cite: 2026-01-22]
    exchange = ccxt.binance({'options': {'defaultType': 'future'}})
    print("✅ تم تشغيل المحرك.. جاري البحث في 50 عملة فيوتشرز...")
    
    # قائمة بـ 50 عملة من الأكثر سيولة في الفيوتشرز
    symbols = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOGE/USDT', 'DOT/USDT', 'LINK/USDT',
        'MATIC/USDT', 'NEAR/USDT', 'LTC/USDT', 'BCH/USDT', 'SHIB/USDT', 'TRX/USDT', 'UNI/USDT', 'XLM/USDT', 'ICP/USDT', 'ETC/USDT',
        'FIL/USDT', 'HBAR/USDT', 'APT/USDT', 'ARB/USDT', 'OP/USDT', 'LDO/USDT', 'RNDR/USDT', 'INJ/USDT', 'TIA/USDT', 'SUI/USDT',
        'PEPE/USDT', 'ORDI/USDT', 'SEI/USDT', 'BEAM/USDT', 'GALA/USDT', 'STX/USDT', 'GRT/USDT', 'AAVE/USDT', 'MKR/USDT', 'SNX/USDT',
        'IMX/USDT', 'ALGO/USDT', 'EGLD/USDT', 'FLOW/USDT', 'RUNE/USDT', 'AXS/USDT', 'SAND/USDT', 'MANA/USDT', 'CHZ/USDT', 'DYDX/USDT'
    ]
    
    while True:
        try:
            for s in symbols:
                # جلب آخر شمعة مكتملة على فريم 15 دقيقة [cite: 2026-01-22]
                ohlcv = exchange.fetch_ohlcv(s, '15m', limit=2)
                if len(ohlcv) < 2: continue
                
                o, h, l, c = ohlcv[0][1], ohlcv[0][2], ohlcv[0][3], ohlcv[0][4]
                
                # 1. شرط اللون: شمعة حمراء [cite: 2026-01-21]
                if c < o:
                    body = o - c
                    u_wick = h - o
                    l_wick = c - l
                    
                    # 2. شرط الذيول والجسم الصارم [cite: 2026-01-21]
                    # ذيل سفلي أطول من العلوي + الجسم أكبر من مجموع الذيول
                    if l_wick > u_wick and body > (u_wick + l_wick):
                        print(f"🎯 صيد ثمين: {s} | شمعة حمراء بذيول مثالية الآن!")
            
            print("🔍 اكتملت دورة الفحص.. إعادة المحاولة خلال 30 ثانية")
            time.sleep(30)
        except Exception as e:
            time.sleep(10)

# تشغيل الرادار في الخلفية
threading.Thread(target=radar_logic, daemon=True).start()

if __name__ == "__main__":
    # تشغيل السيرفر على المنفذ الصحيح لـ Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
