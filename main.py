import ccxt
import time
import os
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- 1. تجنب أخطاء Render (Port Binding) ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar is Running...")

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_port_server, daemon=True).start()

# --- 2. إعدادات بينانس ---
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

# --- 3. قائمة الـ 300 عملة (مكتوبة بالكامل لضمان السرعة) ---
MY_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'LTC/USDT',
    'NEAR/USDT', 'MATIC/USDT', 'OP/USDT', 'ARB/USDT', 'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT',
    'TIA/USDT', 'SEI/USDT', 'SUI/USDT', 'APT/USDT', 'HBAR/USDT', 'ALGO/USDT', 'FIL/USDT', 'ICP/USDT', 'GRT/USDT', 'STX/USDT',
    'INJ/USDT', 'RNDR/USDT', 'FET/USDT', 'AGIX/USDT', 'OCEAN/USDT', 'TAO/USDT', 'THETA/USDT', 'EGLD/USDT', 'AAVE/USDT', 'UNI/USDT',
    'SUSHI/USDT', 'DYDX/USDT', 'CRV/USDT', 'MKR/USDT', 'LDO/USDT', 'PENDLE/USDT', 'ENS/USDT', 'ID/USDT', 'MAV/USDT', 'EDU/USDT',
    'GALA/USDT', 'ORDI/USDT', '1000SATS/USDT', 'BEAMX/USDT', 'PYTH/USDT', 'JUP/USDT', 'STRK/USDT', 'DYM/USDT', 'MANTA/USDT', 'ALT/USDT',
    'ZETA/USDT', 'PIXEL/USDT', 'RONIN/USDT', 'AXS/USDT', 'SAND/USDT', 'MANA/USDT', 'IMX/USDT', 'FLOW/USDT', 'CHZ/USDT', 'ENJ/USDT',
    'YGG/USDT', 'ILV/USDT', 'MAGIC/USDT', 'RUNE/USDT', 'KAS/USDT', 'TWT/USDT', 'GAS/USDT', 'NEO/USDT', 'QTUM/USDT', 'VET/USDT',
    'CFX/USDT', 'KAVA/USDT', 'IOTA/USDT', 'ZIL/USDT', 'ONT/USDT', 'BAT/USDT', 'MASK/USDT', 'LRC/USDT', 'ANKR/USDT', 'LPT/USDT',
    'BLUR/USDT', 'JOE/USDT', 'MINA/USDT', 'WOO/USDT', 'ASTR/USDT', 'GLMR/USDT', 'METIS/USDT', 'QNT/USDT', 'GMX/USDT', 'SNX/USDT',
    '1INCH/USDT', 'AFTY/USDT', 'ALICE/USDT', 'ALPHA/USDT', 'AMB/USDT', 'ANKR/USDT', 'ANT/USDT', 'APE/USDT', 'API3/USDT', 'AR/USDT',
    'ARK/USDT', 'ARKM/USDT', 'ARPA/USDT', 'ATA/USDT', 'ATOM/USDT', 'AUCTION/USDT', 'AUDIO/USDT', 'AXL/USDT', 'BAKE/USDT', 'BAL/USDT',
    'BAND/USDT', 'BEL/USDT', 'BICO/USDT', 'BIGTIME/USDT', 'BLUE/USDT', 'BLZ/USDT', 'BNX/USDT', 'BSV/USDT', 'BSW/USDT', 'C98/USDT',
    'CAKE/USDT', 'CELO/USDT', 'CELR/USDT', 'COMBO/USDT', 'COMP/USDT', 'COTI/USDT', 'CTK/USDT', 'CTSI/USDT', 'CVP/USDT', 'DAR/USDT',
    'DASH/USDT', 'DATA/USDT', 'DENT/USDT', 'DGB/USDT', 'DOCK/USDT', 'DODO/USDT', 'DREP/USDT', 'DUSK/USDT', 'EGLD/USDT', 'EPX/USDT',
    'ERN/USDT', 'ETC/USDT', 'ETHW/USDT', 'FLM/USDT', 'FORTH/USDT', 'FRONT/USDT', 'FTM/USDT', 'FXS/USDT', 'GAL/USDT', 'GHST/USDT',
    'GLM/USDT', 'GMT/USDT', 'GNO/USDT', 'GODS/USDT', 'GTC/USDT', 'HARD/USDT', 'HFT/USDT', 'HIGH/USDT', 'HOOK/USDT', 'HOT/USDT',
    'ICX/USDT', 'IDEX/USDT', 'IMX/USDT', 'IOTX/USDT', 'JOE/USDT', 'KDA/USDT', 'KEY/USDT', 'KNC/USDT', 'KSM/USDT', 'LINA/USDT',
    'LOOM/USDT', 'LPT/USDT', 'LQTY/USDT', 'LSK/USDT', 'LUNC/USDT', 'LUNA/USDT', 'MAV/USDT', 'MDT/USDT', 'MINA/USDT', 'MKR/USDT',
    'MOVR/USDT', 'MTL/USDT', 'MYRIA/USDT', 'NKN/USDT', 'NMR/USDT', 'NTRN/USDT', 'NULS/USDT', 'OGN/USDT', 'OMG/USDT', 'ONG/USDT',
    'OOS/USDT', 'OXT/USDT', 'PAXG/USDT', 'PERP/USDT', 'PHB/USDT', 'PIVX/USDT', 'POL/USDT', 'POLS/USDT', 'POLY/USDT', 'POWR/USDT',
    'PROS/USDT', 'PSG/USDT', 'PUNDIX/USDT', 'PYR/USDT', 'QI/USDT', 'QNT/USDT', 'QUICK/USDT', 'RAD/USDT', 'RARE/USDT', 'RAY/USDT',
    'REEF/USDT', 'REI/USDT', 'REN/USDT', 'REQ/USDT', 'RIF/USDT', 'RLC/USDT', 'ROSE/USDT', 'RSR/USDT', 'RSS3/USDT', 'RVN/USDT',
    'SCRT/USDT', 'SFP/USDT', 'SKL/USDT', 'SLP/USDT', 'SNT/USDT', 'SNX/USDT', 'SPELL/USDT', 'STEEM/USDT', 'STG/USDT', 'STMX/USDT',
    'STORJ/USDT', 'STPT/USDT', 'STRAX/USDT', 'SUN/USDT', 'SXP/USDT', 'SYS/USDT', 'T/USDT', 'THETA/USDT', 'TLM/USDT', 'TRB/USDT',
    'TRU/USDT', 'TRX/USDT', 'UMA/USDT', 'UNFI/USDT', 'USTC/USDT', 'VET/USDT', 'VGX/USDT', 'VIC/USDT', 'VIDT/USDT', 'VITE/USDT',
    'VTHO/USDT', 'WAN/USDT', 'WAVES/USDT', 'WAXP/USDT', 'WIN/USDT', 'WLD/USDT', 'WRX/USDT', 'XEC/USDT', 'XEM/USDT', 'XLM/USDT',
    'XMR/USDT', 'XNO/USDT', 'XVS/USDT', 'XWG/USDT', 'XZE/USDT', 'YFI/USDT', 'YFII/USDT', 'ZEN/USDT', 'ZRX/USDT'
]

# الفريمات المطلوبة
TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']

def check_pattern_in_history(symbol, tf):
    try:
        # جلب 6 شمعات لمسح آخر 5 فرص محتملة
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=6)
        if len(bars) < 3: return False
        
        # فحص كل شمعتين متتاليتين في الـ 5 شمعات الأخيرة
        for i in range(len(bars) - 2):
            c1, c2 = bars[i], bars[i+1]
            o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
            o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]

            # الشروط الصارمة
            if cl1 < o1 and cl2 < o2:
                body1, u1, lt1 = abs(o1-cl1), (h1-max(o1,cl1)), (min(o1,cl1)-l1)
                body2, u2, lt2 = abs(o2-cl2), (h2-max(o2,cl2)), (min(o2,cl2)-l2)

                if body1 > (u1+lt1) and body2 > (u2+lt2):
                    if lt1 > u1 and lt2 > u2:
                        if cl2 < l1: # الإغلاق تحت ذيل الشمعة السابقة
                            return True
        return False
    except: return False

print(f"🚀 الرادار يعمل الآن على {len(MY_SYMBOLS)} عملة يدوية...")

while True:
    try:
        now_header = datetime.now().strftime('%H:%M:%S')
        print(f"\n--- دورة فحص جديدة بدأت: {now_header} ---")
        
        total = len(MY_SYMBOLS)
        for index, symbol in enumerate(MY_SYMBOLS, 1):
            # رسالة الفحص التي تطلبها لا تتوقف أبداً
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"[{current_time}] ({index}/{total}) فحص مستمر: {symbol}")
            
            for tf in TIMEFRAMES:
                if check_pattern_in_history(symbol, tf):
                    print(f"🎯 [فرصة] {symbol} | فريم: {tf}")
            
            time.sleep(0.01) # سرعة عالية جداً
            
        print(f"✅ انتهى الفحص. انتظار دقيقتين...")
        time.sleep(120)
    except Exception as e:
        print(f"❌ خطأ: {e}")
        time.sleep(30)
