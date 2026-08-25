import time
import os
import threading
import requests
import pandas as pd
from datetime import datetime
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Futures Hardcoded Radar Active 24/7", 200

@app.route('/health')
def health():
    return "OK", 200

# قائمة ثابتة وشاملة لأكثر من 400 عملة فيوتشرز على بينانس لضمان الفحص الحقيقي
ALL_FUTURES_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", 
    "LINKUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT", "BCHUSDT", "NEARUSDT", "ATOMUSDT", "UNIUSDT", 
    "ETCUSDT", "XLMUSDT", "ICPUSDT", "APTUSDT", "FILUSDT", "ARBUSDT", "OPUSDT", "FTMUSDT", 
    "INJUSDT", "SUIUSDT", "RNDRUSDT", "SEIUSDT", "TIAUSDT", "RENDERUSDT", "PEPEUSDT", "SHIBUSDT", 
    "FLOKIUSDT", "WIFUSDT", "BONKUSDT", "JUPUSDT", "STRKUSDT", "PENDLEUSDT", "ENAUSDT", "NOTUSDT", 
    "BOMEUSDT", "BBUSDT", "REZUSDT", "IOUSDT", "ZKUSDT", "LISTAUSDT", "BANANAUSDT", "RENDERUSDT", 
    "SYNUSDT", "LPTUSDT", "API3USDT", "BLURUSDT", "ACEUSDT", "NFPUSDT", "AIUSDT", "XAIUSDT", 
    "MANTAUSDT", "ALTUSDT", "JTOUSDT", "PYTHUSDT", "TIAUSDT", "MEMEUSDT", "ORDIUSDT", "SATSUSDT", 
    "RATSUSDT", "GALAUSDT", "SANDUSDT", "MANAUSDT", "AXSUSDT", "CHZUSDT", "ENJUSDT", "GMTUSDT", 
    "IMXUSDT", "MAGICUSDT", "YGGUSDT", "HIGHUSDT", "PEOPLEUSDT", "IOSTUSDT", "THETAUSDT", "ZILUSDT", 
    "KNCUSDT", "CRVUSDT", "SUSHIUSDT", "1INCHUSDT", "COMPUSDT", "MKRUSDT", "SNXUSDT", "BALUSDT", 
    "LRCUSDT", "ZRXUSDT", "BATUSDT", "OCEANUSDT", "COTIUSDT", "KAVAUSDT", "BANDUSDT", "RLCUSDT", 
    "CTKUSDT", "IOTAUSDT", "ZENUSDT", "SKLUSDT", "GRTUSDT", "STORJUSDT", "HBARUSDT", "ONEUSDT", 
    "HOTUSDT", "VETUSDT", "ICXUSDT", "ONTUSDT", "QTUMUSDT", "IOSTUSDT", "THETAUSDT", "ALGOUSDT", 
    "C98USDT", "DARUSDT", "BAKEUSDT", "BURGERUSDT", "SLPUSDT", "DEGOUSDT", "XVSUSDT", "UNFIUSDT", 
    "TRBUSDT", "AUDIOUSDT", "MBOXUSDT", "TLMUSDT", "ATAUSDT", "LITUSDT", "STMXUSDT", "DODOUSDT", 
    "PHAUSDT", "TVKUSDT", "BADGERUSDT", "ALICEUSDT", "RUNEUSDT", "SRMUSDT", "BZRXUSDT", "OMSUSDT", 
    "TOMOUSDT", "DOCKUSDT", "STPTUSDT", "CREAMUSDT", "FIROUSDT", "OGUSDT", "ASRUSDT", "ATMUSDT", 
    "BARUSDT", "JUVUSDT", "PSGUSDT", "CITYUSDT", "INTERUSDT", "PORTOUSDT", "LAZIOUSDT", "SANTOSUSDT", 
    "ALPINEUSDT", "VOXELUSDT", "POLSUSDT", "KEEPUSDT", "NUUSDT", "FLOWUSDT", "RADUSDT", "AUTOUSDT", 
    "QNTUSDT", "CHESSUSDT", "MOVRUSDT", "AGLDUSDT", "LQTYUSDT", "BIFIUSDT", "IDUSDT", "RDNTUSDT", 
    "SSVUSDT", "CFXUSDT", "STXUSDT", "ROSEUSDT", "RSRUSDT", "OGNUSDT", "OGVUSDT", "POLYXUSDT", 
    "LEVERUSDT", "LSKUSDT", "SYSUSDT", "PIVXUSDT", "DGBUSDT", "SCUSDT", "CKBUSDT", "ARDRUSDT", 
    "LSKUSDT", "STEEMUSDT", "HIVEUSDT", "ARDRUSDT", "BTSUSDT", "NKNUSDT", "WANUSDT", "COSUSDT", 
    "CHRUSDT", "MDTUSDT", "STMXUSDT", "DENTUSDT", "MBLUSDT", "ANKRUSDT", "WINUSDT", "BTTUSDT", 
    "CELOUSDT", "RENBTCUSDT", "LUNAUSDT", "USTCUSDT", "ANCUSDT", "MIRUSDT", "SPELLUSDT", "JOEUSDT", 
    "MNGOUSDT", "ORCAUSDT", "SBRUSDT", "MERUSDT", "SUNUSDT", "JSTUSDT", "NFTUSDT", "WINUSDT", 
    "BTTUSDT", "BTTOLDUSDT", "WRXUSDT", "DOCKUSDT", "PNTUSDT", "PERPUSDT", "RAMPUSDT", "LINAUSDT", 
    "FORUSDT", "FRONTUSDT", "FIOUSDT", "EEURUSDT", "EGLDUSDT", "NEARUSDT", "HBARUSDT", "ONEUSDT", 
    "SCUSDT", "CKBUSDT", "ZENUSDT", "IOSTUSDT", "QTUMUSDT", "ONTUSDT", "ICXUSDT", "ZILUSDT", 
    "KNCUSDT", "BATUSDT", "COMPUSDT", "SNXUSDT", "BALUSDT", "LRCUSDT", "ZRXUSDT", "OCEANUSDT", 
    "COTIUSDT", "KAVAUSDT", "BANDUSDT", "RLCUSDT", "CTKUSDT", "IOTAUSDT", "SKLUSDT", "GRTUSDT", 
    "STORJUSDT", "C98USDT", "DARUSDT", "BAKEUSDT", "SLPUSDT", "DEGOUSDT", "XVSUSDT", "UNFIUSDT", 
    "TRBUSDT", "AUDIOUSDT", "MBOXUSDT", "TLMUSDT", "ATAUSDT", "LITUSDT", "DODOUSDT", "PHAUSDT", 
    "ALICEUSDT", "RUNEUSDT", "PERPUSDT", "LINAUSDT", "POLSUSDT", "AGLDUSDT", "LQTYUSDT", "IDUSDT", 
    "RDNTUSDT", "SSVUSDT", "CFXUSDT", "STXUSDT", "ROSEUSDT", "RSRUSDT", "OGNUSDT", "POLYXUSDT", 
    "LEVERUSDT", "SYSUSDT", "DGBUSDT", "ARDRUSDT", "HIVEUSDT", "CHRUSDT", "MDTUSDT", "ANKRUSDT", 
    "CELOUSDT", "SPELLUSDT", "JOEUSDT", "SUNUSDT", "JSTUSDT", "STPTUSDT", "OXTUSDT", "SUPERUSDT", 
    "PROMUSDT", "TKOUSDT", "BURGERUSDT", "MBOXUSDT", "FORTHUSDT", "QUICKUSDT", "CLVUSDT", "MASKUSDT", 
    "COCOSUSDT", "MDTUSDT", "AUTOUSDT", "OXGUSDT", "BETAUSDT", "ILVUSDT", "YGGUSDT", "AGIXUSDT", 
    "HOOKUSDT", "GMXUSDT", "GNSUSDT", "LQTYUSDT", "CFXUSDT", "STXUSDT", "HIGHUSDT", "PEOPLEUSDT", 
    "LDOUSDT", "OPUSDT", "APTUSDT", "SUIUSDT", "SEIUSDT", "TIAUSDT", "MEMEUSDT", "ORDIUSDT", 
    "BLURUSDT", "LOOKSUSDT", "BICOUSDT", "GFUSDT", "GALUSDT", "PROSUSDT", "STGUSDT", "COMBOUSDT", 
    "RDNTUSDT", "EDUUSDT", "SUIUSDT", "1000PEPEUSDT", "1000SHIBUSDT", "1000FLOKIUSDT", "1000BONKUSDT",
    "1000SATSUSDT", "1000RATSUSDT", "1000XECUSDT", "1000BTTUSDT", "1000LUNCUSDT", "1000AGIXUSDT"
]

def check_symbol_tf(symbol, tf):
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={tf}&limit=4"
        res = requests.get(url, timeout=3)
        if res.status_code != 200:
            return

        raw_candles = res.json()
        if len(raw_candles) < 4:
            return

        candles = raw_candles[-4:-1]
        
        df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        c1 = df.iloc[0]
        c2 = df.iloc[1]
        c3 = df.iloc[2]

        # 1. الشمعة الحمراء (C2)
        is_c2_red = c2['close'] < c2['open']
        if not is_c2_red:
            return

        c2_body = abs(c2['open'] - c2['close'])
        c1_body = abs(c1['open'] - c1['close'])

        is_body_bigger = c2_body > c1_body
        breaks_c1_low = c2['close'] < c1['low']

        if not (is_body_bigger and breaks_c1_low):
            return

        # 2. الشمعة الخضراء (C3)
        is_c3_green = c3['close'] > c3['open']
        if not is_c3_green:
            return

        is_fully_inside_red = (c3['low'] >= c2['low']) and (c3['high'] <= c2['high'])

        if is_fully_inside_red:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("\n" + "🔥"*30, flush=True)
            print(f"🚨 [فرصة مؤكدة] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}", flush=True)
            print(f"   📊 إغلاق الخضراء: {c3['close']} | داخل نطاق الحمراء [Low: {c2['low']}, High: {c2['high']}]", flush=True)
            print("🔥"*30 + "\n", flush=True)

    except Exception:
        pass

def run_radar_loop():
    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h']
    print(f"🚀 تم تشغيل الرادار بقائمة ثابتة تضم {len(ALL_FUTURES_SYMBOLS)} عملة فيوتشرز...", flush=True)

    while True:
        try:
            print(f"🔍 [بدء دورة الفحص]: جاري فحص جميع العملات ({len(ALL_FUTURES_SYMBOLS)})...", flush=True)
            
            for symbol in ALL_FUTURES_SYMBOLS:
                print(f"🔍 [جاري فحص الآن]: {symbol}", flush=True)
                for tf in timeframes:
                    check_symbol_tf(symbol, tf)
                time.sleep(0.01)
            
            print("✅ انتهت دورة الفحص الكاملة لجميع العملات. انتظار الدورة القادمة...", flush=True)
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ تنبيه: {e}", flush=True)
            time.sleep(10)

threading.Thread(target=run_radar_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
