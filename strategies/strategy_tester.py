import core.data_manipulator as dm
import json
import strategies.strats as strats
import pandas as pd
from backtesting import Backtest
from multiprocessing import Pool, Manager, cpu_count
from core.logger import log_all_results
from typing import List, Dict, Any, Optional
import time


def load_strategies_from_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as file:
        return json.load(file)

def run_master_backtest(
    symbols: List[str], 
    strategy: str, 
    compare_strategies: bool = False, 
    find_best: bool = False, 
    adaptive_strategy: bool = False, 
    optimize_portfolio: bool = False, 
    adaptive_portfolio: bool = False, 
    plot_results: bool = False
) -> List[Optional[Dict[str, Any]]]:
    with open('data\config.json', 'r') as file:
        config = json.load(file)

    multiple_strategies = config['compare_strategies'] or config['optimize_portfolio'] or config['adaptive_portfolio'] or config['find_best'] or config['adaptive_strategy']
    new_results = False
    
    if (config['plot_results'] and len(symbols) > 10) or not plot_results:
        config['plot_results'] = False
        
    with Manager() as manager:
        strategies = manager.dict(load_strategies_from_json('strategies\strategies.json'))
        community_strategies = manager.dict(load_strategies_from_json('strategies\community_strategies.json'))
        strategies.update(community_strategies)
        # strategies = manager.dict({'Buy_After_Red_Day': 0})
        stock_data = manager.dict(dm.fetch_data_or_load_cached(symbols))

        if multiple_strategies:
            results = dm.load_cached_results(symbols, strategies.keys())
            new_results = results is None
        else:
            results = None

        symbols = list(stock_data.keys())

        if results is None:
            with Pool(min(len(symbols), cpu_count())) as pool:
                if config['compare_strategies'] or compare_strategies or config['optimize_portfolio'] or optimize_portfolio or config['adaptive_portfolio'] or adaptive_portfolio:
                    results = pool.starmap(run_backtest_process, [(stock_data, symbol, strategy, config['plot_results']) for symbol in symbols for strategy in strategies.keys()])
                elif config['find_best'] or find_best:
                    results = pool.starmap(find_best_backtest, [(stock_data, symbol, strategies, config['plot_results']) for symbol in symbols])
                elif config['adaptive_strategy'] or adaptive_strategy:
                    results = pool.starmap(run_adaptive_backtest, [(stock_data, symbol, strategies, config['plot_results']) for symbol in symbols])
                else:
                    results = pool.starmap(run_backtest_process, [(stock_data, symbol, strategy, config['plot_results']) for symbol in symbols])

        strategies = dict(strategies)

    results = [result for result in results if result is not None]

    if config['sort_results']:
        results = sorted(results, key=lambda x: x[config['sorting_criteria']])
    
    log_all_results(results, strategies, find_best, optimize_portfolio, adaptive_portfolio)

    if multiple_strategies and new_results:
        dm.save_results(results, list(strategies.keys()))

    return results

def run_backtest(
    stock_data: Dict[str, pd.DataFrame], 
    symbol: str, 
    strategy: str, 
    plot: bool = False, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    start_percent: float = 0, 
    end_percent: float = 1
) -> Optional[Dict[str, Any]]:
    if stock_data[symbol] is None:
        return None
    
    if start_date is not None and end_date is not None:
        df = dm.fetch_data(symbol, start_date, end_date)
    else:
        df = stock_data[symbol].copy()

    start_index = int(start_percent * len(df))
    end_index = int(end_percent * len(df))
    df = df.iloc[start_index:end_index]
    size = 0.5

    df = dm.create_signals(df, strategy)
    result = gather_backtest_result(df, symbol, strategy, size, plot)

    if result is None:
        print(f"Backtest for {symbol} with strategy -{strategy}- failed or no trades were made.")
        return None

    return result

def run_backtest_process(
    stock_data: Dict[str, pd.DataFrame], 
    symbol: str, 
    strategy: str, 
    plot: bool = False
) -> Optional[Dict[str, Any]]:
    result = run_backtest(stock_data, symbol, strategy, plot)
    
    if result is None:
        return None
    
    simplified_result = dm.generate_simple_result(symbol, strategy, result)

    return simplified_result

def find_best_backtest(
    stock_data: Dict[str, pd.DataFrame], 
    symbol: str, 
    strategies: Dict[str, int], 
    plot: bool = False, 
    start_percent: float = 0, 
    end_percent: float = 1
) -> Optional[Dict[str, Any]]:
    best_strategy = None
    best_result = None
    best_sharpe = 0

    for strategy in strategies.keys():
        result = run_backtest(stock_data, symbol, strategy, plot, start_percent=start_percent, end_percent=end_percent)

        if result is None:
            continue
        
        if result['Sharpe Ratio'] > best_sharpe:
            best_result = result
            best_sharpe = result['Sharpe Ratio']
            best_strategy = strategy
    
    if best_strategy is not None:
        strategies[best_strategy] += 1

    else:
        return None

    simplified_result = dm.generate_simple_result(symbol, best_strategy, best_result)

    return simplified_result

def run_adaptive_backtest(
    stock_data: Dict[str, pd.DataFrame], 
    symbol: str, 
    strategies: Dict[str, int], 
    plot: bool = False, 
    start_percent: float = 0, 
    end_percent: float = 0.5
) -> Optional[Dict[str, Any]]:
    results = find_best_backtest(stock_data, symbol, strategies, plot, start_percent=start_percent, end_percent=end_percent)

    if results is None:
        return None
    
    strategy = results['strategy']
    
    result = run_backtest(stock_data, symbol, strategy, plot, start_percent=end_percent, end_percent=1)
    simplified_result = dm.generate_simple_result(symbol, strategy, result)

    return simplified_result

def gather_backtest_result(
    df: pd.DataFrame, 
    symbol: str, 
    strategy: str, 
    size: float, 
    plot: bool = False
) -> Optional[Dict[str, Any]]:
    try:
        bt = Backtest(df, strats.load_strategy(strategy, df, size), cash=100000, margin=1/1, commission=0.00025)

    except Exception as e:
        print(f"Error running backtest for {symbol}: {e}")
        return None
        
    result = bt.run()

    if plot:
        bt.plot(resample=False)

    if result['# Trades'] == 0:
        return None
    
    return result
