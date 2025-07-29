import pandas as pd
from stratdev.backend.ohlc import GetOHLC
from stratdev.utils import ohlc_agg

'''
Credit to HariSeldon2020 and WorkPiece from r/RealDayTrading for coming up with the calculation.
Calculates "Real Relative Strength" of an asset compared to the overall market
'''

    #Wilder's Average Calculation (Needed for ATR Calculation)
def WildersAverage(values, n):
    return values.ewm(alpha=1 / n, adjust=False).mean()

    #ATR Calculation
def atr(df, n=14):
    data = df.copy()
    high = data['High']
    low = data['Low']
    close = data['Close']
    data['tr0'] = (high - low)
    data['tr1'] = abs(high - close.shift())
    data['tr2'] = abs(low - close.shift())
    tr = data[['tr0', 'tr1', 'tr2']].shift().max(axis=1)
    atr = WildersAverage(tr, n)

    return atr

# Real Relative Strength calculation
def rrs(df: pd.DataFrame, mkt: pd.DataFrame, rrs_length: int, shift: int=0) -> pd.Series:

    # Rolling move
    mkt_r = mkt.Close - mkt.Close.shift(rrs_length)
    df_r = df.Close - df.Close.shift(rrs_length)
    
    # ATR
    mkt_atr = atr(mkt, n=rrs_length)
    df_atr = atr(df, n=rrs_length)

    # Real Relative Strength calculation
    power_index = mkt_r / mkt_atr
    expected_move = power_index * df_atr
    diff = df_r - expected_move
    real_relative_strength = round(diff / df_atr, 3)

    rrs = pd.Series(real_relative_strength, index=df.Close.index).shift(shift)

    return rrs

def daily_rrs(df: pd.DataFrame, mkt: pd.DataFrame, rrs_length: int, shift: int=0) -> pd.Series:
    daily = df.resample('1d').apply(ohlc_agg).dropna()
    daily_mkt = mkt.resample('1d').apply(ohlc_agg).dropna()
    daily['rrs_d1'] = rrs(daily,daily_mkt,rrs_length,shift)
    filtered_daily = daily[['rrs_d1']]

    merged = pd.merge_asof(df, filtered_daily, left_index=True, right_index=True)

    return merged

