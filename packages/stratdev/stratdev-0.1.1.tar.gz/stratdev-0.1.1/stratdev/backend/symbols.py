import requests
from bs4 import BeautifulSoup as bs

"""
Lists of ticker symbols corresponding to various ETFs
"""

# Get ETF holdings function
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


# Top 50 holdings for major market ETFs

spy50 = get_etf_holdings('spy')
qqq50 = get_etf_holdings('qqq')
dia50 = get_etf_holdings('dia')
iwm50 = get_etf_holdings('iwm')

# Small sample of tickers per major market ETF

SPY = ['SPY','MSFT','NVDA','AAPL','AMZN','META','GOOGL','V','AVGO', 'JPM','TSLA','XOM', 'UNH']

QQQ = ['QQQ','AAPL','MSFT','NVDA','AMZN','AVGO','META','TSLA','GOOGL','COST','NFLX','ADBE','AMD']

DIA = ['DIA','UNH','GS','MSFT','HD','CAT','AMGN','CRM','V','MCD','AXP','AAPL','TRV']

IWM = ['IWM','INSM','FTAI','PCVX','SFM','FLR','AIT','FN','ENSG','MLI','UFPI','SPSC','SSB']

etf_list = ['SPY','QQQ','DIA','IWM']

# Top tickers included in each SPDR sector ETF

XLK = ['XLK','MSFT','AAPL','AVGO','AMD','ADBE','CRM','QCOM','ORCL','AMAT','CSCO','ACN','TXN','IBM','INTU']
XLC = ['XLC','META','GOOGL','CMCSA','T','EA','VZ','TMUS','NFLX','DIS','TTWO','OMC','WBD','LYV','CHTR','MTCH']
XLY = ['XLY','AMZN','TSLA','HD','MCD','TJX','LOW','NKE','SBUX','CMG','ABNB','MAR','GM', 'AZO', 'ROST']
XLP = ['XLP','PG','COST','WMT','KO','PM','PEP','MDLZ','MO','CL','TGT','KMB','STZ','KR','MNST','GIS']
XLF = ['XLY','JPM','V','MA','BAC','WFC','GS','AXP','MS','C','SCHW','MMC','PGR', 'BLK', 'CB']
XLE = ['XLE','XOM','CVX','EOG','SLB','COP','PSX','MPC','WMB','VLO','HES','OXY','FANG','OKE','BKR']
XLU = ['XLU','NEE','SO','DUK','CEG','SRE','AEP','D','PEG','PCG','EXC','ED','VST','EIX','AWK']
XLI = ['XLI','GE','CAT','UBER','HON','UNP','ETN','UPS','ADP','BA','DE','TT','WM']

# Lists of lists

sector_names = ['XLK','XLC','XLY','XLP','XLF','XLE','XLU','XLI']
spdr_sectors = [XLK,XLC,XLY,XLP,XLF,XLE,XLU,XLI]

