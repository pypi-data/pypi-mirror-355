import pandas as pd

def pivots(df:pd.DataFrame, length: int, shift: int=None) -> pd.DataFrame:

    """Basic algorithm for finding price swing highs and lows. Somewhat
    useful for identifying breakouts or support and resistance"""
    
    if shift == None:
        shift = 0
    else:
        shift=shift

    # Price highs and lows
    highs = df.High
    lows = df.Low

    # Pivot highs and lows lists
    pivot_highs = []
    pivot_lows = []

    # Check if high/low price is highest/lowest of last {length} values and next {length} values
    for i in range(length, len(df) - length):
        if (
            highs.iloc[i] > max(highs.iloc[i - length : i])
            and highs.iloc[i] > max(highs.iloc[i + 1 : i + length + 1])
        ):
            pivot_highs.append(i)
        if (
            lows.iloc[i] < min(lows.iloc[i - length : i])
            and lows.iloc[i] < min(lows.iloc[i + 1 : i + length + 1])
        ):
            pivot_lows.append(i)

    # Columns for pivot highs and lows
    df['pivot_highs'] = highs.iloc[pivot_highs]
    df['pivot_lows'] = lows.iloc[pivot_lows]

    # Shift pivot values to avoid look-ahead bias
    df['pivot_highs'] = df['pivot_highs'].shift(shift)
    df['pivot_lows'] = df['pivot_lows'].shift(shift)
    
    # Forward fill pivot price
    df['pivot_highs'] = df['pivot_highs'].ffill()
    df['pivot_lows'] = df['pivot_lows'].ffill()

    return df