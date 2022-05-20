from matplotlib import style
import requests
import time
import pandas
import ta
import mplfinance as mpf

# return finished caldles only (no current candle)


def get_candles(symbol: str, timeframe: str = '1h', limit: int = 500):  # 1h 4h 1d
    candles = requests.get("https://api.binance.com/api/v3/klines",
                           params={"symbol": symbol, "limit": limit, "interval": timeframe})
    return candles  # candles[-1] is newest (not current)


def cal_tech(df):
    df['K'] = ta.momentum.stoch(
        df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    df['D'] = df['K'].rolling(3).mean()
    df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
    df.dropna(inplace=True)
    return df


def plot(df):
    #vlines = dict(vlines=['2022-04-30 15:00:00',
                 #         '2022-05-20 15:00:00'], linewidths=(1))
    #print(vlines)
    #alines_points = [('2022-04-30 15:00:00', 24.178654), ('2022-05-20 15:00:00', 39.397142)]
    mpf.plot(df, type='candle', volume=False, style='yahoo')


candles = get_candles('KDAUSDT', '1h', 1000).json()
df = pandas.DataFrame(candles).iloc[0:-1, 0:6]
df.columns = ['Open time', 'Open', 'High', 'Low', 'Close', 'Volume']
df = df.set_index('Open time')
df.index = pandas.to_datetime(df.index, unit='ms')
df = df.astype(float)
df = cal_tech(df)
print(df.tail())
signal = df.query('(rsi > 70 & K > 80 & D > 80) | (rsi < 30 & K < 20 & D < 20)')
#print(signal)
#plot(signal)

# tenical analysis + percentage rebalance(>10%, 5%)
# ema 30 50 (trading ciew) stoch rsi(<>70 && cross) + rsi(<>50)
# EMA 10 ตัดกับ EMA 21  หากเส้น EMA 10 ตัดขึ้นซื้อเพิ่มเพราะมันลงมาสุดแล้ว ส่วน EMA 10 ตัดลงเราก็ขาย เพราะมันขึ้นมาสุดแล้ว โดยใช้ TIME FRAME DAY
