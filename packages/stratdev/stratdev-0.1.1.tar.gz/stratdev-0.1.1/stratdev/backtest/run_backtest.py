import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from stratdev.backend.bt import BacktestingPy
from stratdev.backtest import analysis

# Export Paths 
htmls = './htmls/'
trades = './trades/'
stats = './stats/'
pdfs = './pdfs/'

def run_backtest(strategy: object,
                symbols: dict,
                msc:str,
                cash:int=10000,
                comission:float=0.0,
                margin:float=1.0,
                trade_on_close:bool=False,
                hedging:bool=False,
                exclusive_orders:bool=False,
                ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Runs multi-ticker backtest of chosen strategy on chosen symbols. Results of backtest are
    saved to appropriate folders.
    All analysis functions in analysis.py are also performed on backtest results, the output
    of these analysis functions are saved in appropriate folder(s).
    """
    # Backtest initialization
    btpy = BacktestingPy(strategy, symbols, html_path=htmls, stats_path=stats, trades_path=trades)

    # Multi-ticker backtest 
    bt_stats, bt_trades, bt_equity_curves = btpy.multi_ticker_backtest(cash=cash,
                                                                       commission=comission,
                                                                       margin=margin,
                                                                       trade_on_close=trade_on_close,
                                                                       hedging=hedging,
                                                                       exclusive_orders=exclusive_orders)

    # Analysis
    bt_return_v_dd = analysis.returns_vs_drawdowns(btpy, bt_stats)
    bt_ec_plot = analysis.plot_equity_curves(btpy, bt_equity_curves)
    bt_ratios = analysis.ratios(btpy, bt_stats)

    # Export to pdf
    with PdfPages(f'{pdfs}returns_vs_drawdowns_{msc}.pdf') as pdf:
        pdf.savefig(bt_return_v_dd)

    with PdfPages(f'{pdfs}equity_curves_{msc}.pdf') as pdf:
        pdf.savefig(bt_ec_plot)

    with PdfPages(f'{pdfs}ratios_{msc}.pdf') as pdf:
        pdf.savefig(bt_ratios)

    return bt_stats, bt_trades, bt_equity_curves

