import time
import os
import requests
import pandas as pd
from datetime import datetime
from flask import Flask
from concurrent.futures import ThreadPoolExecutor
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Binance Precise Radar Active 24/7", 200

@app.route('/health')
def health():
    return "OK", 200

ALL_FUTURES_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", 
    "LINKUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT", "BCHUSDT", "NEARUSDT", "ATOMUSDT", "UNIUSDT", 
    "ETCUSDT", "XLMUSDT", "ICPUSDT", "APTUSDT", "FILUSDT", "ARBUSDT", "OPUSDT", "FTMUSDT", 
    "INJUSDT", "SUIUSDT", "RNDRUSDT", "SEIUSDT", "TIAUSDT", "RENDERUSDT", "PEPEUSDT", "SHIBUSDT", 
    "FLOKIUSDT", "WIFUSDT", "BONKUSDT", "JUPUSDT", "STRKUSDT", "PENDLEUSDT", "ENAUSDT", "NOTUSDT", 
    "BOMEUSDT", "BBUSDT", "REZUSDT", "IOUSDT", "ZKUSDT", "LISTAUSDT", "BANANAUSDT", "SYNUSDT", 
    "LPTUSDT", "API3USDT", "BLURUSDT", "ACEUSDT", "NFPUSDT", "AIUSDT", "XAIUSDT", "MANTAUSDT", 
    "ALTUSDT", "JTOUSDT", "PYTHUSDT", "MEMEUSDT", "ORDIUSDT", "SATSUSDT", "RATSUSDT", "GALAUSDT", 
    "SANDUSDT", "MANAUSDT", "AXSUSDT", "CHZUSDT", "ENJUSDT", "GMTUSDT", "IMXUSDT", "MAGICUSDT", 
    "YGGUSDT", "HIGHUSDT", "PEOPLEUSDT", "IOSTUSDT", "THETAUSDT", "ZILUSDT", "KNCUSDT", "CRVUSDT", 
    "SUSHIUSDT", "1INCHUSDT", "COMPUSDT", "MKRUSDT", "SNXUSDT", "BALUSDT", "LRCUSDT", "ZRXUSDT", 
    "BATUSDT", "OCEANUSDT", "COTIUSDT", "KAVAUSDT", "BANDUSDT", "RLCUSDT", "CTKUSDT", "IOTAUSDT", 
    "ZENUSDT", "SKLUSDT", "GRTUSDT", "STORJUSDT", "HBARUSDT", "ONEUSDT", "HOTUSDT", "VETUSDT", 
    "ICXUSDT", "ONTUSDT", "QTUMUSDT", "ALGOUSDT", "C98USDT", "DARUSDT", "BAKEUSDT", "SLPUSDT", 
    "DEGOUSDT", "XVSUSDT", "UNFIUSDT", "TRBUSDT", "AUDIOUSDT", "MBOXUSDT", "TLMUSDT", "ATAUSDT", 
    "LITUSDT", "STMXUSDT", "DODOUSDT", "PHAUSDT", "ALICEUSDT", "RUNEUSDT", "PERPUSDT", "LINAUSDT", 
    "POLSUSDT", "AGLDUSDT", "LQTYUSDT", "IDUSDT", "RDNTUSDT", "SSVUSDT", "CFXUSDT", "STXUSDT", 
    "ROSEUSDT", "RSRUSDT", "OGNUSDT", "POLYXUSDT", "LEVERUSDT", "SYSUSDT", "DGBUSDT", "ARDRUSDT", 
    "HIVEUSDT", "CHRUSDT", "MDTUSDT", "ANKRUSDT", "CELOUSDT", "SPELLUSDT", "JOEUSDT", "SUNUSDT", 
    "JSTUSDT", "STPTUSDT", "LDOUSDT", "OPUSDT", "APTUSDT", "SUIUSDT", "SEIUSDT", "TIAUSDT", 
    "1000PEPEUSDT", "1000SHIBUSDT", "1000FLOKIUSDT", "1000BONKUSDT", "1000SATSUSDT", "1000RATSUSDT"
]

def check_symbol_tf(symbol):
    # نركز على فريم 1m و 3m و 5m كما في صورتك
    timeframes = ['1m', '3m', '5m']
    for tf in timeframes:
        try:
            # نسحب آخر 15 شمعة لنفحص بدقة الشموع الأخيرة المغلقة
            url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={tf}&limit=15"
            res = requests.get(url, timeout=2)
            if res.status_code != 200:
                continue

            raw_candles = res.json()
            if len(raw_candles) < 5:
                continue

            df = pd.DataFrame(raw_candles, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
            
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)

            # نفحص الشموع من الخلف إلى الأمام
            for i in range(len(df) - 1, 1, -1):
                c1 = df.iloc[i - 1] # الشمعة الحمراء الكاسرة
                c2 = df.iloc[i]     # الشمعة الخضراء المحتواة

                # 1. الشمعة الأولى يجب أن تكون حمراء (إغلاق أقل من افتتاح)
                is_c1_red = c1['close'] < c1['open']
                if not is_c1_red:
                    continue

                # 2. الشمعة الثانية يجب أن تكون خضراء (إغلاق أعلى من افتتاح)
                is_c2_green = c2['close'] > c2['open']
                if not is_c2_green:
                    continue

                # 3. الشرط الأساسي: الشمعة الخضراء محتواة بالكامل داخل نطاق الشمعة الحمراء التي قبلها
                # (قاع الخضراء >= قاع الحمراء، وقمتها <= قمة الحمراء)
                is_fully_inside = (c2['low'] >= c1['low']) and (c2['high'] <= c1['high'])

                if is_fully_inside:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print("\n" + "🔥"*30, flush=True)
                    print(f"🚨 [تم رصد النموذج بدقة] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}", flush=True)
                    print(f"   📊 الحمراء [Low: {c1['low']}, High: {c1['high']}] | الخضراء المحتواة [Low: {c2['low']}, High: {c2['high']}]", flush=True)
                    print("🔥"*30 + "\n", flush=True)
                    return

        except Exception:
            pass

def run_radar_loop():
    print(f"🚀 بدء التشغيل بالدقة المطلوبة للمستطيل ({len(ALL_FUTURES_SYMBOLS)} عملة)...", flush=True)
    while True:
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(check_symbol_tf, ALL_FUTURES_SYMBOLS)
        time.sleep(5)

threading.Thread(target=run_radar_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
