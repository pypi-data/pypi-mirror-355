import pandas as pd
import pandas_ta as ta
from stratdev.utils import ohlc_agg


def atr_high_low(df:pd.DataFrame, length:int=14, include_daily_atr:bool=False) -> pd.DataFrame:
    """
    Adds daily ATR High and Low levels to OHLC DataFrame. ATR High/Low range is calculated from
    previous daily closing price.
    """
    # Resample DataFrame's timeframe to daily OHLC
    daily = df.resample('1d').apply(ohlc_agg).dropna()

    # ATR, ATR High, ATR Low calculations
    daily['atr'] = round(ta.atr(daily.High, daily.Low, daily.Close, length),2)
    daily['atr_high'] = (daily.Close + (daily['atr'] / 2)).shift(1)
    daily['atr_low'] = (daily.Close - (daily['atr'] / 2)).shift(1)
    
    # Filter for ATR, high and low
    if include_daily_atr:
        filtered_daily = daily[['atr','atr_high','atr_low']]
    else:
        filtered_daily = daily[['atr_high','atr_low']]

    # Integrate ATR high and low levels into original DataFrame
    merged = pd.merge_asof(df, filtered_daily, left_index=True, right_index=True)

    return merged


