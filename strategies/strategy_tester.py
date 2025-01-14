import core.data_manipulator as dm
import core.logger as logger
import strategies.strats as strats
from backtesting import Backtest
from multiprocessing import Pool, Manager, cpu_count
import json


def load_strategies_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def run_master_backtest(symbols, strategy):
    with open('data\config.json', 'r') as file:
        config = json.load(file)
    
    if config['plot_results'] and len(symbols) > 10:
        print("Too many symbols to plot results for.")
        config['plot_results'] = False
        
    # Create a multiprocessing manager and shared dictionary for strategies
    with Manager() as manager:
        # Shared dict that processes can safely update
        strategies = manager.dict(load_strategies_from_json('strategies\strategies.json'))
        community_strategies = manager.dict(load_strategies_from_json('strategies\community_strategies.json'))
        strategies.update(community_strategies)

        # Use Pool to parallelize the backtest process
        with Pool(min(len(symbols), cpu_count())) as pool:
            # Run backtest in parallel and get the results
            if config['compare_strategies']:
                results = pool.starmap(run_backtest_process, [(symbol, strategy, config['plot_results']) for symbol in symbols for strategy in strategies.keys()])

            elif config['find_best']:
                results = pool.starmap(find_best_backtest, [(symbol, strategies, config['plot_results']) for symbol in symbols])

            elif config['adaptive_strategy']:
                results = pool.starmap(run_adaptive_backtest, [(symbol, strategies, config['plot_results']) for symbol in symbols])

            else:
                results = pool.starmap(run_backtest_process, [(symbol, strategy, config['plot_results']) for symbol in symbols])

        # After all backtests are done, log the aggregated results
        results = [result for result in results if result is not None]

        if config['sort_results']:
            results = sorted(results, key=lambda x: x[config['sorting_criteria']], reverse=True)

        for result in results:
            logger.log_simple(result)

        if config['find_best']:
            logger.compare_results(strategies)

        logger.log_aggregated_results(results)

def run_backtest(symbol, strategy, plot = False, start_date = None, end_date = None, start_percent = 0, end_percent = 1):
    df = dm.fetch_data(symbol, start_date, end_date)
    
    if df is None:
        return None
    
    start_index = int(start_percent * len(df))
    end_index = int(end_percent * len(df))
    df = df.iloc[start_index:end_index]
    size = 0.5

    dm.create_signals(df, strategy)
    results = gather_backtest_results(df, strategy, size, plot)
    
    if results is None:
        print(f"Backtest for {symbol} with strategy -{strategy}- failed or no trades were made.")
        return None

    return results

def run_backtest_process(symbol, strategy, plot = False):
    result = run_backtest(symbol, strategy, plot)
    
    if result is None:
        return None
    
    # Convert result to a dictionary or other simple format
    simplified_result = dm.generate_simple_result(symbol, strategy, result)

    return simplified_result

def find_best_backtest(symbol, strategies, plot = False, start_percent = 0, end_percent = 1):
    best_strategy = None
    best_result = None
    best_sharpe = 0

    for strategy in strategies.keys():
        result = run_backtest(symbol, strategy, plot, start_percent=start_percent, end_percent=end_percent)

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

def run_adaptive_backtest(symbol, strategies, plot = False, start_percent = 0, end_percent = 0.5):
    results = find_best_backtest(symbol, strategies, plot, start_percent=start_percent, end_percent=end_percent)

    if results is None:
        return None
    
    strategy = results['strategy']
    
    result = run_backtest(symbol, strategy, plot, start_percent=end_percent, end_percent=1)
    simplified_result = dm.generate_simple_result(symbol, strategy, result)

    return simplified_result

def gather_backtest_results(df, strategy, size, plot = False):
    try:
        bt = Backtest(df, strats.load_strategy(strategy, df, size), cash=100000, margin=1/1, commission=0.0001)

    except Exception as e:
        print(f"Error running backtest: {e}")
        return None
        
    results = bt.run()

    if plot:
        bt.plot(resample=False)

    if results['# Trades'] == 0:
        return None
    
    return results