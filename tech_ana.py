import pandas as pd
import ta
import mplfinance as mpf
import requests


def get_candles(symbol: str, timeframe: str, limit: int = 1000):  # 1h 4h 1d
    candles = requests.get("https://api.binance.com/api/v3/klines",
                           params={"symbol": symbol, "limit": limit, "interval": timeframe}).json()
    df = pd.DataFrame(candles).iloc[0:-1, 0:6]
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    df = df.astype(float)
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    #df = df.set_index('time')
    #df.index = pandas.to_datetime(df.index, unit='ms')
    return df


def signal(df: pd.DataFrame, rsi_length: int = 14, arn_length: int = 25, reversal_check_length: int = 40, vortex_length: int = 20):
    # calculate indicator
    df['rsi'] = ta.momentum.rsi(df['close'], window=rsi_length)
    arn = ta.trend.AroonIndicator(df['close'], window=arn_length)
    df['arn_up'] = arn.aroon_up()
    df['arn_down'] = arn.aroon_down()
    """
    ema1 = ta.trend.EMAIndicator(df['close'], window=100)
    df['ema1'] = ema1.ema_indicator()
    ema2 = ta.trend.EMAIndicator(df['close'], window=200)
    df['ema2'] = ema2.ema_indicator()
    vt = ta.trend.VortexIndicator(
        df['high'], df['low'], df['close'], window=vortex_length)
    df['vt_pos'] = vt.vortex_indicator_pos()
    df['vt_neg'] = vt.vortex_indicator_neg()
    atr = ta.volatility.AverageTrueRange(
        df['high'], df['low'], df['close'], window=14)
    df['atr'] = atr.average_true_range()
    """

    # signal
    arn_cross = []
    for i, r in df.iterrows():
        # check ema cross
        if i > 0:  # skip index 0
            arn_up_l = df.iloc[i-1, 7]
            arn_down_l = df.iloc[i-1, 8]
            # cross up > down = 1
            if (arn_up_l < arn_down_l) & (r['arn_up'] > r['arn_down']):
                arn_cross.append(1)
            # cross down > up = 2
            elif (arn_up_l > arn_down_l) & (r['arn_up'] < r['arn_down']):
                arn_cross.append(2)
            else:
                arn_cross.append(0)
        else:
            arn_cross.append(0)
    df['arn_cross'] = pd.Series(arn_cross)
    # reversal
    reversal = []
    for i, r in df.iterrows():
        if (r['arn_cross'] == 1) & (i > reversal_check_length):  # down => up
            for j in range(i-reversal_check_length, i):
                if (df.iloc[j, 6] < 30):  # up
                    reversal.append(1)
                    break
                if (j == i-1):
                    reversal.append(0)
        elif (r['arn_cross'] == 2) & (i > reversal_check_length):  # up => down
            for j in range(i-reversal_check_length, i):
                if (df.iloc[j, 6] > 70):
                    reversal.append(2)  # down
                    break
                if (j == i-1):
                    reversal.append(0)
        else:
            reversal.append(0)
    df['reversal'] = pd.Series(reversal)
    return df


def plot(df: pd.DataFrame, symbol: str, timeframe: str):
    # setup
    sig_up = df.query('reversal == 1')
    sig_down = df.query('reversal == 2')
    vl_up = dict(
        vlines=sig_up["datetime"].tolist(), linewidths=1, colors='g')
    vl_down = dict(
        vlines=sig_down["datetime"].tolist(), linewidths=1, colors='r')
    df = df.set_index('datetime')

    # style
    # Create my own `marketcolors` to use with the `nightclouds` style:
    mc = mpf.make_marketcolors(up='#00ff00', down='#ff00ff', inherit=True)

    # Create a new style based on `nightclouds` but with my own `marketcolors`:
    s = mpf.make_mpf_style(
        base_mpl_style=['dark_background', 'bmh'], marketcolors=mc)

    # Plot
    mpf.plot(df, type='candle', volume=False,
             title="\n"+symbol+" "+timeframe+"\nBottom Signals", style=s, vlines=vl_up)
    mpf.plot(df, type='candle', volume=False,
             title="\n"+symbol+" "+timeframe+"\nTop Signals", style=s, vlines=vl_down)


def check_ta(symbol: str, timeframe: str):
    df = get_candles(symbol, timeframe, 160)
    df = signal(df, 17, 18, 30)
    df.to_csv("check_ta.csv")
    if int(df.iloc[-1,-1]) > 0:
        return True
    return False



symbol = "FLUXUSDT"
timeframe = '4h'
df = get_candles(symbol, timeframe, 1000)
# print(df)
#df = signal_1(df, 14, 10, 15, 50)
df = signal(df, 14, 14, 30)
# df.to_csv("t.csv")
print(df)
plot(df, symbol, timeframe)


# EMA10 & 15 cross + rsi backward check + chg%

