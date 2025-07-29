import os
import subprocess
from stratdev.utils import create_file

"""
Creates a new session folder and populates folder with necessary python files for backtesting.

- start.py: creates necessary folders and initiates ohlc download process.
- data_prep.py: basic template for data prep phase, use this file to add relevant indicators/data to
ohlc dataframe.
- strategy.py: basic template for composing a strategy with backtesting.py's Strategy class
- backtest.py: run backtest
"""

# Pre-written content for python files

new_download = (
"""
import stratdev.session.start
"""
)

data_prep = (
"""
import pandas_ta as ta
from stratdev.utils import ticker_list, dataframes
from stratdev.backend.ohlc import GetOHLC

# Paths for OHLC data, period, interval
raw_ohlc = './ohlc/raw_ohlc/'
updated_ohlc = './ohlc/updated_ohlc/'
period = ''
interval = ''

# List of tickers
tickers = ticker_list(raw_ohlc)

# Read in raw dataframes, add indicators, save to csv
for ticker in tickers:
    df = GetOHLC(ticker, period, interval).from_clean_csv(raw_ohlc)
    # update dataframe columns / manipulate or clean data as needed
    df.to_csv(f'{updated_ohlc}{ticker}_{period}_{interval}_updated.csv')

# Read in updated dataframes, store in dictionary
dfs = dataframes(updated_ohlc, tickers)"""
)

strategy = (
"""
import pandas as pd
from datetime import datetime, time
from backtesting import Strategy, Backtest
from backtesting.lib import resample_apply
import pandas_ta as ta


class StratName(Strategy):
    """
    
    """

    def init(self):
        pass


    def next(self):

        price = self.data.Close[-1]


        if not self.position:
            pass
"""
)

backtest = (
"""
from stratdev.backtest.run_backtest import run_backtest
from strategy import StratName 
from data_prep import dfs 

run_backtest(StratName, dfs)
"""
)


def new_session():
    # Create new session
    while True:
        try:
            start_new = input("Create new backtesting session? Y/N: ")
            if start_new.lower() == 'y' or start_new.lower() == 'n':
                break
            else:
                print('Invalid input. Choose Y or N')
        except ValueError:
            pass
            continue
    
    if start_new == 'n':
        return
    
    # Input folder name for session
    else:
        while True:
            try:
                folder_name = input("\nName of folder: ")
                if not os.path.isdir(folder_name):
                    break
                else:
                    print('Folder name already exists')
            except ValueError:
                pass
                continue

        # Create session folder
        try:
            os.mkdir(f'{folder_name}')
        except FileExistsError:
            print(f"Folder '{folder_name}' already exists.")
        except OSError as e:
            print(f"Error creating folder '{folder_name}' : {e}")

        # Create files in session folder
        filenames = ['new_download','data_prep','strategy', 'backtest']
        files = [new_download, data_prep, strategy, backtest]

        for name, content in zip(filenames, files):
            create_file(name, content, folder_name)

        # Start session
        while True:
            try:
                start_session = input("\nstart session? Y/N: \n")
                if start_session.lower() == 'y' or start_session.lower() == 'n':
                    break
                else:
                    print('Invalid input. Choose Y or N')
            except ValueError:
                pass
                continue
        if start_session == 'n':
            return
        
        else:
            os.chdir(folder_name)   # change directory to session folder
            subprocess.run(['python3', 'new_download.py'])     # run new_download.py
            # os.system('/bin/bash')      # artificially change directory to session folder 
            
new_session()
# if __name__ == '__main__':
#     new_session()




