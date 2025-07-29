import re
import os
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv

from alpaca.data.historical import StockHistoricalDataClient 
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

import yfinance as yf

from stratdev.utils import ohlc_agg

load_dotenv()
API_KEY = os.environ.get('API_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')


class GetOHLC:
    """
    Download OHLC data using either yfinance or alpaca APIs.
     
    Returns clean dataframe with datetime as index and converts index to pandas datetime object 
    to be compatible with backtesting.py's backtesting framework
    """

    def __init__(self, 
                 symbol: str,           # ticker symbol. Format: 'ABC' (All caps)
                 period: str = '5y',    # lookback period from the end date, end date defaults to most recent trading day. 
                 interval: str = '1d',  # bar size
                 start: str = None,     # start date. Format: (YYYY-MM-DD) 
                 end: str = None,       # end date. Format: (YYYY-MM-DD)
                 path: str = None       # Path for csv
                ):

     
        self.symbol = symbol
        self.period = period
        self.interval = interval 
        self.start = start
        self.end = end
        self.path = path
        self.two_decimals = pd.Series([2,2,2,2], index=['Open', 'High','Low','Close']) # rounds OHLC data to two decimal places

    
    def from_yfinance(self) -> pd.DataFrame:
        
        """
        Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo 

        1m data cannot extend past 7 days
        2m - 30m data, and 90m data cannot extend past 60 days
        1h data cannot extend past 730 days
        1d - 3mo data allows max available data
        """

        # Start and end date specified
        if self.start != None and self.end != None:
            download = yf.download(self.symbol, period=self.period, interval=self.interval,
                               start=self.start, end=self.end, auto_adjust=False, 
                               progress=False, prepost=False)
        
        # Start and end date is None
        else: 
            download = yf.download(self.symbol, period=self.period, interval=self.interval,
                                auto_adjust=False, progress=False, prepost=False)

        # Round OHLC data to two decimal places, drop unneeded column, convert index to pd.datetime format 
        df = download.round(self.two_decimals)
        df.drop(columns='Adj Close', inplace=True)
        df.index = pd.to_datetime(download.index)

        if not self.path:
            return df
        
        else:
            df.to_csv(f'{self.symbol}_{self.period}_{self.interval}.csv')
            
        return df
    

    def from_alpaca(self) -> pd.DataFrame:
        
        """
        As of 2024, data from 2016 to present (8 years) is available for all intervals.
        """
        # API and Secret Key, initialize historical data client
        api_key = API_KEY
        secret_key = SECRET_KEY
        client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
    
        # Daily OHLCV requested
        if self.interval == '1d':

        # Start and end dates specified
            if self.start != None and self.end != None:
                start_date = self.start
                end_date = self.end

        # Start and end date not specified, period is in year ('y')
            elif self.start == None and self.end == None and 'y' in self.period:
                num_years = re.split('(\\d+)', self.period)
                start_date = date.today() - timedelta(days=365*int(num_years[1]))
                end_date = date.today()
                
        # Start and end date not specified, period is in days ('d')
            elif self.start == None and self.end == None and 'd' in self.period:
                num_days = re.split('(\\d+)', self.period)
                start_date = date.today() - timedelta(days=int(num_days[1]))
                end_date = date.today()
            
        # Start and end date not specified, no period specified, default period is 5 years
            else: 
                start_date = date.today() - timedelta(days=1825)
                end_date = date.today()

        # Request daily bars
            request_params = StockBarsRequest(
            symbol_or_symbols = self.symbol,
            timeframe=TimeFrame.Day,
            adjustment="split",
            start=start_date,
            end=end_date
            )

        # Raw DataFrame
            stock = client.get_stock_bars(request_params)
            raw_data = stock.df

        # OHLC data rounded two decimal places, index renamed and set to pd.datetime format, unneeded columns dropped
            df = raw_data.reset_index(level=0, drop=True)
            df = df.round(self.two_decimals)
            df.rename(columns={'open':'Open','high':'High',
                                'low':'Low','close':'Close',
                                'volume':'Volume'}, inplace=True)
            df.index = pd.to_datetime(df.index).strftime('%Y-%m-%d')
            df.index = pd.to_datetime(df.index)
            df.drop(columns=['trade_count','vwap'], inplace=True)
            df.index.names = ['Date']
            df['Volume'] = df['Volume'].astype(int)

            if not self.path:
                return df
        
            else:
                df.to_csv(f'{self.symbol}_{self.period}_{self.interval}.csv')
            
            return df
        
        # Intraday OHLCV requested
        else:
        
        # Start and end datetimes specified
            if self.start != None and self.end != None:

                start_datetime = pd.to_datetime(self.start, utc=True)
                end_datetime = pd.to_datetime(self.end, utc=True)

        # Request year-to-date's worth of data
            elif self.start == None and self.end == None and self.period == 'ytd':
                start_datetime = date.today() - timedelta(days=365)
                end_datetime = date.today()

        # Request user defined number of years worth of data
            elif self.start == None and self.end == None and 'y' in self.period:
                num_years = re.split('(\\d+)', self.period)
                start_datetime=date.today() - timedelta(days=365*int(num_years[1]))
                end_datetime = date.today()
            
        # Request user defined number of days worth of data
            elif self.start == None and self.end == None and self.period != None:
                num_days = re.split('(\\d+)', self.period)
                start_datetime = date.today() - timedelta(days=int(num_days[1]))
                end_datetime = date.today()

        # Request user defined number of days from specified end date
            elif self.start == None and self.end != None and self.period != None:
                if 'y' in self.period:
                    num_years = re.split('(\\d+)', self.period)
                    end_datetime = pd.to_datetime(self.end)
                    start_datetime = end_datetime - timedelta(days=365*int(num_years[1]))
                else:
                    num_days = re.split('(\\d+)', self.period)
                    end_datetime = pd.to_datetime(self.end)
                    start_datetime = end_datetime - timedelta(days=int(num_days[1]))

        # If no start or end datetime given, default to 100 days worth of data
            else:
                start_datetime = date.today() - timedelta(days=100)
                end_datetime = date.today()

            """
            '1h' data needs to be imported as 30min data then resampled,
            otherwise data starts at 09:00am.

            Hourly data more than '1h' not yet supported. ie '2h', '4h' etc.
            """

            if self.interval == '1h' or self.interval == '30m':
                amount = 30
                end = '15:30'

            if 'h' in self.interval and int(re.split('(\\d+)', self.interval)[1]) > 1:
                raise ValueError(f'Houlry data higher than 1 hour not supported, attempted input: {self.interval}')

        # Intraday interval determines last printed time value i.e '5m' data ends at 15:55
            else: 
                res = re.split('(\\d+)', self.interval)
                amount = int(res[1])
                endtime = timedelta(hours=16, minutes=00)
                end = str(endtime - timedelta(minutes=amount))
   
        # Request intraday bars
            request_params = StockBarsRequest(
                symbol_or_symbols = self.symbol,
                timeframe=TimeFrame(amount=amount, unit=TimeFrameUnit.Minute),
                adjustment="split",
                start=start_datetime,
                end=end_datetime
            )

        # Raw DataFrame
            stock = client.get_stock_bars(request_params)
            raw_data = stock.df

        # Reset index, fix timezone, set index to pd.datetime format, rename index
            df = raw_data.reset_index(level=0, drop=True)
            df = df[~df.index.duplicated(keep='first')]         # in case of duplicate index
            df.index = pd.to_datetime(df.index).strftime('%Y-%m-%d %H:%M:%S')
            df.index = pd.to_datetime(df.index)
            df.index = df.index.tz_localize('UTC').tz_convert('US/Eastern')
            df.index = df.index.tz_localize(None)
            df.index.names = ['Datetime']

        # Fix column names, drop unneeded columns
            df = df.drop(columns=['trade_count','vwap'])
            df = df.rename(columns={'open':'Open','high':'High',
                            'low':'Low','close':'Close',
                            'volume':'Volume'})

        # Convert Volume column to integer format
            df['Volume'] = df['Volume'].astype(int)

        # Round OHLC data to two decimals
            df = df.round(self.two_decimals)

        # Filter data to only show ohlcv during open market hours (9:30 - 4:00)
            df = df.between_time('09:30', end)
            # print(df.head())

        # Resample 30m to 1h
            if self.interval == '1h':
                df = df.resample('1h', offset='30Min').apply(ohlc_agg).dropna().between_time('09:30', '15:30')

            if not self.path:
                return df
        
            else:
                df.to_csv(f'{self.symbol}_{self.period}_{self.interval}.csv')
        
        return df

            

    def from_clean_csv(self,
                      csv_path: str,                  # Path of csv being read in  
                      msc: str='',                    # Misc string after symbol if any               
                      ) -> pd.DataFrame:
        
        """Reads in previously cleaned OHLC csv file while keeping datetime as index, and converts
        index to pandas datetime object to be compatible with backtest.py's backtesting framework"""

        """
        Method assumes OHLC csv being read in is saved in the following format:
        [path][symbol][optional string].csv

        ex. /Users/user/csv_files/AAPLdaily.csv
        """
        
        df = pd.read_csv(f'{csv_path}{self.symbol}_{self.period}_{self.interval}{msc}.csv', index_col=[0])
        df.index = pd.to_datetime(df.index)

        return df
