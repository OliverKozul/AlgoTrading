from core.data_manipulator import load_symbols
from strategies.strategy_tester import run_master_backtest
import random


if __name__ == "__main__":
    symbols = load_symbols('SP')
    # symbols = ['SPY']
    # symbols = ['TSLA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NFLX', 'NVDA', 'AMD']
    # symbols = load_symbols('futures')
    symbols = random.sample(symbols, min(len(symbols), 50))
    strategy = 'Buy_After_Red_Day'
    
    run_master_backtest(symbols, strategy)
