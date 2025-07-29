from stratdev.session.download import download_ohlc
from stratdev.utils import create_folders

'''
Meant to be used at the start of a backtesting session to 
create all necessary folders, as well as download and save 
the initial OHLC data that will later be manipulated and 
analyzed for specific backtesting needs.
'''

create_folders()
download_ohlc()