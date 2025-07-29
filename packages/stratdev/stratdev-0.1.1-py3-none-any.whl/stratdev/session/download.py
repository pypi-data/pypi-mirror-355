import os
import json
from datetime import datetime
import importlib
import stratdev
from stratdev.authenticate import authenticate_alpaca
from stratdev.backend.ohlc import GetOHLC
from stratdev.backend.symbols import *


'''
Meant to be used at the start of a backtesting session to download and save the initial OHLC data
that will later be manipulated and analyzed for specific backtesting needs.

Downloads historical OHLC data for a symbol or list of symbols. 
Symbol or list of symbols, lookback period, and time interval are all specified by user input.
'''

def download_ohlc(ohlc_path: str='./ohlc/'):
    # Symbol list
    symbols = []

    # Acceptable period and interval
    period_accept = ['y','d']
    interval_accept = ['m','h','d']


    # Choose Single Ticker or Multi-Ticker
    while True:
        try:
            print('\n')
            single_multi = input('Download data for one symbol (1) or multiple symbols? (2): ')
            if int(single_multi) == 1 or int(single_multi) == 2:
                break
            else:
                print('Invalid choice. Please choose 1 or 2.')
        except ValueError:
            print('Invalid input')
            continue


    # Single Ticker chosen
    if int(single_multi) == 1:
        while True:
            try:
                print('\n')
                symbol = input('Enter symbol: ').strip().upper()
                if len(symbol) <= 5:
                    break
                else:
                    print('You may have entered an invalid symbol, try again')
            except ValueError:
                continue
    

    # Multi-Ticker Chosen, Choose Pre-made or Custom list
    elif  int(single_multi) == 2:
        while True:
            try:
                print('\n')
                multi = input('Pre-made list of symbols (1) or custom? (2): ')
                if int(multi) == 1 or int(multi) == 2:
                    break
                else:
                    print('Invalid choice. Please choose 1 or 2.')
            except ValueError:
                print('Invalid input')
                continue
            
        # Pre-made list chosen
        """
        Pre-made lists are those defined in symbols.py. Input should be name of variable
        desired list is stored in
        """
        if int(multi) == 1:
            while True:
                try:
                    print('\n')
                    symbols_req = input('Choose symbol list: ').strip().upper()
                    if symbols_req in etf_list or symbols_req in sector_names:
                        symbols = globals()[symbols_req]
                        break
                    else:
                        print('Invalid list of symbols.')
                except ValueError:
                    print('Invalid input')
                    continue

        # Custom list chosen
        if int(multi) == 2:
            while True:
                try:
                    print('\n')
                    json_manual = input('Get symbol list from JSON (1) or input manually? (2): ')
                    if int(json_manual) == 1 or int(json_manual) == 2:
                        break
                    else:
                        print('Invalid choice. Please choose 1 or 2.')
                except ValueError:
                    print('Invalid input')
                    continue
                
            if int(json_manual) == 1:
                while True:
                    try:
                        print('\n')
                        file = input('Enter JSON file name without extension: ').strip()
                        if os.path.isfile(f'{file}.json'):
                            with open(f'{file}.json', 'r') as json_file:
                                symbols = json.load(json_file)
                            break
                        else:
                            print('File is not in current directory')
                    except FileNotFoundError:
                        print('File not found')
                        continue
                    
            if int(json_manual) == 2:
                while True:
                    try:
                        print('\n')
                        symbol_list = input('Enter symbols (comma separated): ').strip().upper()
                        symbols = [x.strip() for x in symbol_list.split(',')]
                        if symbols:
                            break
                        else:
                            print('You must enter at least one symbol.')
                    except ValueError:
                        continue


    # Choose source
    while True:
        env_path = stratdev.__file__[:-11] + 'backend'
        backend_files = [f for f in os.listdir(env_path)]
        try:
            print('\n')
            source = input('Source (1 for alpaca, 2 for yfinance): ')
            if int(source) == 1 and '.env' not in backend_files:
                authenticate_alpaca()
                importlib.reload(stratdev.backend.ohlc)
                break
            elif int(source) == 1 or int(source) == 2:
                break
            else:
                print('Invalid choice. Please choose 1 or 2.')
        except ValueError:
            print('Invalid Input')
            continue


    # Choose period, interval
    while True:
        try:
            print('\n')
            period = input('Period: ')
            print('\n')
            interval = input('Interval: ')

            # Write period and interval into data_prep.py
            with open('./data_prep.py', 'r') as file:
                lines = file.readlines()

            new_period = f"period = '{period}'"
            new_interval = f"interval = '{interval}'"
            lines[9 - 1] = new_period + '\n'
            lines[10 - 1] = new_interval + '\n'

            with open('./data_prep.py', 'w') as file:
                file.writelines(lines)
                
            # Validity check
            if (
                any(p in period for p in period_accept) and
                any(i in interval for i in interval_accept) and
                len(period) <= 3 and
                len(interval) <= 4
                ):
                break
            else:
                print(
                    'Invalid input. Please check input for correct ticker, period, and interval', '\n',
                    'Valid periods: "y", "d"', '\n',
                    'Valid intervals:  "m", "h", "d"', '\n'
                )
        except ValueError:
            continue


    # Choose start and end date
    while True:
        if 'd' in interval:
            format =  '%Y-%m-%d'
            print('\n')
            start_input = input('Start date (YYYY-MM-DD) Leave blank if none: ')
            print('\n')
            end_input =  input('End date (YYYY-MM-DD) Leave blank if none: ')
        else:
            format = '%Y-%m-%d %H:%M:%S'
            print('\n')
            start_input = input('Start date (YYYY-MM-DD HH:MM:SS) Leave blank if none: ')
            print('\n')
            end_input =  input('End date (YYYY-MM-DD HH:MM:SS) Leave blank if none: ')

        if start_input == '' and end_input == '':
            start_date = None
            end_date = None
            break

        elif  start_input == '' and end_input != '':
            start_date = None
            try:
                end_date = datetime.strptime(end_input, format)
                break
            except ValueError:
                print('Invalid datetime format. Please use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS')

        elif start_input != '' and end_input != '':
            try:
                start_date = datetime.strptime(start_input, format)
                end_date = datetime.strptime(end_input, format)
                break
            except ValueError:
                print('Invalid datetime format. Please use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS')
        
        else:
            print('Check Start Date and End Date inputs and try again. Something is wrong.')
            continue


    # Download OHLC data, save as CSV
    print('\n')
    print('Downloading OHLC data...')

    if int(single_multi) == 2:

        if int(source) == 1:
            for symbol in symbols:
                df = GetOHLC(symbol, period, interval, start_date, end_date).from_alpaca()
                df.to_csv(f'{ohlc_path}/raw_ohlc/{symbol}_{period}_{interval}.csv')

        elif int(source) == 2:
            for symbol in symbols:
                df = GetOHLC(symbol, period, interval, start_date, end_date).from_yfinance()
                df.to_csv(f'{ohlc_path}/raw_ohlc/{symbol}_{period}_{interval}.csv')
    
    else:
        if int(source) == 1:
            df = GetOHLC(symbol, period, interval, start_date, end_date).from_alpaca()
        elif int(source) == 2:
            df = GetOHLC(symbol, period, interval, start_date, end_date).from_yfinance()

        df.to_csv(f'{ohlc_path}{symbol}_{period}_{interval}.csv')

    print('Download complete.')


