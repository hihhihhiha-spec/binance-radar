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
    return "Binance Futures Advanced Radar Active 24/7", 200

@app.route('/health')
def health():
    return "OK", 200

# قائمة العملات الكاملة
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

def check_symbol_tf(symbol, tf):
    try:
        # نطلب آخر 20 شمعة لنفحص التاريخ القريب بالكامل ولا نفوت أي فرصة
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={tf}&limit=20"
        res = requests.get(url, timeout=3)
        if res.status_code != 200:
            return

        raw_candles = res.json()
        if len(raw_candles) < 5:
            return

        df = pd.DataFrame(raw_candles, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        # نفحص الشموع من الخلف إلى الأمام لنرى إن كان النموذج قد تحقق في أي من الشموع السابقة
        for i in range(len(df) - 1, 2, -1):
            c1 = df.iloc[i - 2]
            c2 = df.iloc[i - 1]
            c3 = df.iloc[i]

            # 1. الشمعة الحمراء (C2)
            is_c2_red = c2['close'] < c2['open']
            if not is_c2_red:
                continue

            c2_body = abs(c2['open'] - c2['close'])
            c1_body = abs(c1['open'] - c1['close'])

            is_body_bigger = c2_body > c1_body
            breaks_c1_low = c2['close'] < c1['low']

            if not (is_body_bigger and breaks_c1_low):
                continue

            # 2. الشمعة الخضراء (C3)
            is_c3_green = c3['close'] > c3['open']
            if not is_c3_green:
                continue

            is_fully_inside_red = (c3['low'] >= c2['low']) and (c3['high'] <= c2['high'])

            if is_fully_inside_red:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("\n" + "🔥"*30, flush=True)
                print(f"🚨 [فرصة مؤكدة تم رصدها] | العملة: {symbol} | الفريم: {tf} | الوقت: {now}", flush=True)
                print(f"   📊 إغلاق الخضراء: {c3['close']} | داخل نطاق الحمراء [Low: {c2['low']}, High: {c2['high']}]", flush=True)
                print("🔥"*30 + "\n", flush=True)
                break # وجدنا النموذج في هذه العملة، ننتقل للتي بعدها

    except Exception:
        pass

def run_radar_loop():
    timeframes = ['1m', '3m', '5m', '15m', '30m', '1h']
    print(f"🚀 تم تشغيل الرادار المطور لفحص التاريخ القريب ({len(ALL_FUTURES_SYMBOLS)} عملة)...", flush=True)

    while True:
        try:
            print(f"🔍 [بدء دورة فحص عميق]: جاري فحص العملات...", flush=True)
            
            for symbol in ALL_FUTURES_SYMBOLS:
                for tf in timeframes:
                    check_symbol_tf(symbol, tf)
                time.sleep(0.01)
            
            print("✅ انتهت دورة الفحص العميق. التكرار قريباً...", flush=True)
            time.sleep(15)

        except Exception as e:
            print(f"⚠️ تنبيه: {e}", flush=True)
            time.sleep(10)

threading.Thread(target=run_radar_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
