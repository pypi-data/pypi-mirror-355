import pandas as pd


def range_breach(df:pd.DataFrame,
                        less:str, 
                        greater:str,
                        breach_direction:str) -> pd.DataFrame:
    """
    Adds a column to OHLC DataFrame that shows whether a breach has occured between 
    09:30:00(Market open) to 15:55:00(Market close) each day. If a breach has occured at any 
    point intraday, column returns True from moment of breach until end of day. 
    Conditions reset every new day.

    To show breach of range high: less = 'range_high', greater = 'Close'
    To show breach of range low: less = 'Close', greater = 'range_low'
    """
    # Breach boolean column
    df[f'breach_{breach_direction}'] = df[greater] > df[less]
    
    # Masks
    forward_fill_mask= df[f'breach_{breach_direction}'].copy()
    reset_mask = df.index.time == pd.to_datetime('9:30').time()

    # Iterate through DataFrame
    for i in range(1, len(df)):
        if forward_fill_mask.iloc[i-1] and not reset_mask[i]:
            forward_fill_mask.iloc[i] = True
    
    # Forward fill True if breach from time of breach to end of day
    df[f'breach_{breach_direction}'] = forward_fill_mask

    return df




    