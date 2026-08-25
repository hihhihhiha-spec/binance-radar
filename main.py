import ccxt
import time
import os
import threading
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- إعدادات تيليجرام (مجهزة بالبيانات الخاصة بك) ---
TELEGRAM_TOKEN = "8866274181:AAEU7Ofsem4EW87PNo1Uk_sNs0VSejcSmvI"
CHAT_ID = "6141474899"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Send Error: {e}", flush=True)

# --- 1. حل مشكلة توقف Render (يمنع السيرفر من النوم) ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar is Active")
    def log_message(self, format, *args): return

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_port_server, daemon=True).start()

# --- 2. إعدادات بينانس (تفعيل ميزة الـ Rate Limit المدمجة في CCXT) ---
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True  # هذه تطلب من المكتبة تنظيم الطلبات تلقائياً لتجنب الحظر
})

# --- 3. قائمة الـ 300 عملة ---
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
    '1INCH/USDT', 'ALICE/USDT', 'ALPHA/USDT', 'AMB/USDT', 'APE/USDT', 'API3/USDT', 'AR/USDT', 'ARK/USDT', 'ARKM/USDT', 'ARPA/USDT',
    'ATA/USDT', 'ATOM/USDT', 'AUCTION/USDT', 'AUDIO/USDT', 'AXL/USDT', 'BAKE/USDT', 'BAL/USDT', 'BAND/USDT', 'BEL/USDT', 'BICO/USDT',
    'BIGTIME/USDT', 'BLZ/USDT', 'BNX/USDT', 'BSV/USDT', 'BSW/USDT', 'C98/USDT', 'CAKE/USDT', 'CELO/USDT', 'CELR/USDT', 'COMBO/USDT',
    'COMP/USDT', 'COTI/USDT', 'CTK/USDT', 'CTSI/USDT', 'CVP/USDT', 'DAR/USDT', 'DASH/USDT', 'DATA/USDT', 'DENT/USDT', 'DGB/USDT',
    'DOCK/USDT', 'DODO/USDT', 'DUSK/USDT', 'EPX/USDT', 'ERN/USDT', 'ETC/USDT', 'FLM/USDT', 'FRONT/USDT', 'FTM/USDT', 'FXS/USDT',
    'GAL/USDT', 'GHST/USDT', 'GLM/USDT', 'GMT/USDT', 'GNO/USDT', 'GTC/USDT', 'HARD/USDT', 'HFT/USDT', 'HIGH/USDT', 'HOOK/USDT',
    'HOT/USDT', 'ICX/USDT', 'IDEX/USDT', 'IOTX/USDT', 'KEY/USDT', 'KNC/USDT', 'KSM/USDT', 'LINA/USDT', 'LOOM/USDT', 'LQTY/USDT',
    'LSK/USDT', 'LUNC/USDT', 'LUNA/USDT', 'MDT/USDT', 'MOVR/USDT', 'MTL/USDT', 'NKN/USDT', 'NMR/USDT', 'NTRN/USDT', 'NULS/USDT',
    'OGN/USDT', 'OMG/USDT', 'ONG/USDT', 'OXT/USDT', 'PAXG/USDT', 'PERP/USDT', 'PHB/USDT', 'PIVX/USDT', 'POL/USDT', 'POLS/USDT',
    'POWR/USDT', 'PROS/USDT', 'PSG/USDT', 'PUNDIX/USDT', 'PYR/USDT', 'QI/USDT', 'QUICK/USDT', 'RAD/USDT', 'RARE/USDT', 'RAY/USDT',
    'REEF/USDT', 'REI/USDT', 'REN/USDT', 'REQ/USDT', 'RIF/USDT', 'RLC/USDT', 'ROSE/USDT', 'RSR/USDT', 'RSS3/USDT', 'RVN/USDT',
    'SCRT/USDT', 'SFP/USDT', 'SKL/USDT', 'SLP/USDT', 'SNT/USDT', 'SPELL/USDT', 'STEEM/USDT', 'STG/USDT', 'STMX/USDT', 'STORJ/USDT',
    'STPT/USDT', 'STRAX/USDT', 'SUN/USDT', 'SXP/USDT', 'SYS/USDT', 'T/USDT', 'TLM/USDT', 'TRB/USDT', 'TRU/USDT', 'TRX/USDT',
    'UMA/USDT', 'UNFI/USDT', 'USTC/USDT', 'VGX/USDT', 'VIC/USDT', 'VIDT/USDT', 'VITE/USDT', 'VTHO/USDT', 'WAN/USDT', 'WAVES/USDT',
    'WAXP/USDT', 'WIN/USDT', 'WLD/USDT', 'WRX/USDT', 'XEC/USDT', 'XEM/USDT', 'XLM/USDT', 'XMR/USDT', 'XNO/USDT', 'XVS/USDT',
    'XWG/USDT', 'XZE/USDT', 'YFI/USDT', 'YFII/USDT', 'ZEN/USDT', 'ZRX/USDT', 'AEVO/USDT', 'NFP/USDT', 'XAI/USDT', 'AI/USDT',
    'MYRO/USDT', 'PORTAL/USDT', 'VANRY/USDT', 'GNS/USDT', '1000BONK/USDT', 'SATS/USDT', 'ORDI/USDT', 'RATS/USDT'
]

TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '4h']

def check_logic(symbol, tf):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=7)
        if len(bars) < 6: 
            return False
        
        for i in range(len(bars) - 2):
            c1, c2, c3 = bars[i], bars[i+1], bars[i+2]
            
            o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
            o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]
            o3, h3, l3, cl3 = c3[1], c3[2], c3[3], c3[4]
            
            is_red_1 = cl1 < o1
            is_red_2 = cl2 < o2
            body2 = abs(o2 - cl2)
            lower_wick2 = min(o2, cl2) - l2
            cond_candle_2 = (is_red_2 and body2 > 0 and body2 > lower_wick2)
            
            is_green_3 = cl3 > o3
            body2_top = max(o2, cl2)
            body2_bottom = min(o2, cl2)
            body3_top = max(o3, cl3)
            body3_bottom = min(o3, cl3)
            
            is_inside_body = (is_green_3 and body3_top <= body2_top and body3_bottom >= body2_bottom)
            
            if is_red_1 and cond_candle_2 and is_inside_body:
                print(f"🎯 MATCH FOUND! {symbol} on timeframe {tf}", flush=True)
                return True
                
        return False
    except Exception as e:
        # طباعة المشكلة دون توقف البوت
        return False

print(f"🚀 Radar Started safely with Rate Limit: {len(MY_SYMBOLS)} symbols.", flush=True)
send_telegram_message("🚀 تم إعادة تشغيل الرادار مع تنظيم الطلبات تلقائياً لتفادي الحظر تماماً.")

while True:
    try:
        for index, symbol in enumerate(MY_SYMBOLS, 1):
            for tf in TIMEFRAMES:
                if check_logic(symbol, tf):
                    alert_msg = f"🎯 *تنبيه رادار بينانس!*\n\n🔹 العملة: `{symbol}`\n⏱️ الفريم: `{tf}`\n⏰ الوقت: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                    print(f"ALERT FOUND: {symbol} | {tf}", flush=True)
                    send_telegram_message(alert_msg)
                
                # توقف آمن ومدروس بعد كل فريم لمنع استهلاك نقاط بينانس
                time.sleep(0.25)
            
            # توقف إضافي قصير بعد الانتهاء من كل عملة كاملة
            time.sleep(0.5)
        
        print("--- Cycle Finished. Restarting Now ---", flush=True)
        time.sleep(15)
    except Exception as e:
        print(f"Main Loop Error: {e}", flush=True)
        time.sleep(30)
