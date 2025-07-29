import os
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs

"""
Various functions to be used throughout the backtesting process
"""

def create_folders(path: str='', names: list[str]=None, for_backtesting: bool=True):
    """Create necessary folders for backtesting session"""
    if for_backtesting:
        names = ['ohlc','htmls','stats','trades','pdfs']
    else: names = names

    # Create Main folders
    for name in names:
        try:
            os.mkdir(f'{path}{name}')
            print(f"Folder '{name}' created successfully.")
        except FileExistsError:
            print(f"Folder '{name}' found.")
        except OSError as e:
            print(f"Error creating folder '{name}' : {e}")

    # Create ohlc subfolders
    try:
        os.mkdir(f'./ohlc/raw_ohlc')
        os.mkdir(f'./ohlc/updated_ohlc')
    except FileExistsError:
        pass
    except OSError as e:
        print(f"An Error occured while creating subfolders: {e}")


def create_file(name, content, folder):
    """Create Python file with pre-written content"""
    with open(f'./{folder}/{name}.py', 'w') as f:
        f.write(content)


def get_etf_holdings(etf: str) -> list:
    """Get Top ~50 holdings of selected ETF"""
    url = f"https://stockanalysis.com/etf/{etf}/holdings/"
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = bs(response.text, 'html.parser')
    table = soup.find('table')
    tickers = table.find_all('a')
    tickers_clean = [x.text.strip() for x in tickers]
    if 'BRK.B' in tickers_clean:
        tickers_clean.remove('BRK.B')

    return tickers_clean


def ticker_list(path: str) -> list:
    """Store ticker names from downloaded csvs to a list"""
    tickers = []
    for file in os.listdir(path):
        split_file = file.split('_')
        if split_file[0] not in tickers:
            tickers.append(split_file[0])
        else:
            continue

    return tickers


def dataframes(path: str, tickers: list[str]) -> dict:
    """Read in ohlc dataframes from csv, store in a dictionary"""
    dataframes = {}
    for file, ticker in zip(os.listdir(path), tickers):
        dataframes[ticker] = pd.read_csv(f'{path}{file}', index_col=[0])
        dataframes[ticker].index = pd.to_datetime(dataframes[ticker].index)

    return dataframes

"""For resampling OHLC to different time interval"""
ohlc_agg = {
'Open': 'first',
'High': 'max',
'Low': 'min',
'Close': 'last',
'Volume': 'sum'
}

def resample_df(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample OHLCV data to desired time interavl"""    
    resample = df.resample(timeframe).apply(ohlc_agg).dropna()
    return resample



 
