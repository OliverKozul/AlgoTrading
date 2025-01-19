import core.data_manipulator as dm
import core.logger as logger
import strategies.strats as strats
from backtesting import Backtest
from multiprocessing import Pool, Manager, cpu_count
import json


# stock_data = {}

def load_strategies_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def run_master_backtest(symbols, strategy, compare_strategies = False, find_best = False, adaptive_strategy = False, plot_results = False, sort_results = False, sorting_criteria = 'Sharpe Ratio'):
    with open('data\config.json', 'r') as file:
        config = json.load(file)
    
    if config['plot_results'] and len(symbols) > 10:
        print("Too many symbols to plot results for.")
        config['plot_results'] = False
        
    with Manager() as manager:
        strategies = manager.dict(load_strategies_from_json('strategies\strategies.json'))
        community_strategies = manager.dict(load_strategies_from_json('strategies\community_strategies.json'))
        strategies.update(community_strategies)

        with Pool(min(len(symbols), cpu_count())) as pool:
            stock_data = manager.dict({symbol: dm.fetch_data(symbol) for symbol in symbols})

            if config['compare_strategies'] or compare_strategies:
                results = pool.starmap(run_backtest_process, [(stock_data, symbol, strategy, config['plot_results']) for symbol in symbols for strategy in strategies.keys()])
            elif config['find_best'] or find_best:
                results = pool.starmap(find_best_backtest, [(stock_data, symbol, strategies, config['plot_results']) for symbol in symbols])
            elif config['adaptive_strategy'] or adaptive_strategy:
                results = pool.starmap(run_adaptive_backtest, [(stock_data, symbol, strategies, config['plot_results']) for symbol in symbols])
            else:
                results = pool.starmap(run_backtest_process, [(stock_data, symbol, strategy, config['plot_results']) for symbol in symbols])

        results = [result for result in results if result is not None]

        if config['sort_results']:
            results = sorted(results, key=lambda x: x[config['sorting_criteria']], reverse=True)

        for result in results:
            logger.log_simple(result)

        if config['find_best']:
            logger.compare_results(strategies)

        logger.log_aggregated_results(results)

        return results

def run_backtest(stock_data, symbol, strategy, plot = False, start_date = None, end_date = None, start_percent = 0, end_percent = 1):
    if stock_data is None or stock_data.get(symbol) is None:
        stock_data[symbol] = dm.fetch_data(symbol, start_date, end_date)

    df = stock_data[symbol].copy()
    
    if df is None:
        return None
    
    start_index = int(start_percent * len(df))
    end_index = int(end_percent * len(df))
    df = df.iloc[start_index:end_index]
    size = 0.5

    dm.create_signals(df, strategy)
    result = gather_backtest_result(df, symbol, strategy, size, plot)

    # for i in range(1, 10):
    #     print(f"Achieved average returns of: {round(dm.calculate_n_day_returns(df, i), 4)}% over the course of {i} days. {symbol} with strategy -{strategy}-")
    
    if result is None:
        print(f"Backtest for {symbol} with strategy -{strategy}- failed or no trades were made.")
        return None

    return result

def run_backtest_process(stock_data, symbol, strategy, plot = False):
    result = run_backtest(stock_data, symbol, strategy, plot)
    
    if result is None:
        return None
    
    simplified_result = dm.generate_simple_result(symbol, strategy, result)

    return simplified_result

def find_best_backtest(stock_data, symbol, strategies, plot = False, start_percent = 0, end_percent = 1):
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

def run_adaptive_backtest(stock_data, symbol, strategies, plot = False, start_percent = 0, end_percent = 0.5):
    results = find_best_backtest(stock_data, symbol, strategies, plot, start_percent=start_percent, end_percent=end_percent)

    if results is None:
        return None
    
    strategy = results['strategy']
    
    result = run_backtest(stock_data, symbol, strategy, plot, start_percent=end_percent, end_percent=1)
    simplified_result = dm.generate_simple_result(symbol, strategy, result)

    return simplified_result

def gather_backtest_result(df, symbol, strategy, size, plot = False):
    try:
        bt = Backtest(df, strats.load_strategy(strategy, df, size), cash=100000, margin=1/1, commission=0.0001)

    except Exception as e:
        print(f"Error running backtest for {symbol}: {e}")
        return None
        
    result = bt.run()

    if plot:
        bt.plot(resample=False)

    if result['# Trades'] == 0:
        return None
    
    return result
