from core.data_manipulator import load_symbols
from strategies.strategy_tester import run_master_backtest


if __name__ == "__main__":
    symbols = load_symbols('SP')
    # symbols = ['ES=F', 'YM=F', 'NQ=F', 'RTY=F', 'ZB=F', 'GC=F', 'SI=F']
    # symbols = load_symbols('futures')
    strategy = 'Daily_Range'
    
    run_master_backtest(symbols, strategy)
