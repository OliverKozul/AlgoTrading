from core.data_manipulator import load_symbols
from strategies.strategy_tester import run_master_backtest
import random


if __name__ == "__main__":
    # SP for S&P500, NQ for Nasdaq, R2000 for Russell 2000
    # symbols = load_symbols('SP')
    symbols = ['SPY', 'QQQ']
    # symbols = ['TSLA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NFLX', 'NVDA', 'AMD']
    # symbols = load_symbols('futures')
    # symbols = random.sample(symbols, min(len(symbols), 25))
    strategy = 'ROC_Mean_Reversion'
    
    run_master_backtest(symbols, strategy)
