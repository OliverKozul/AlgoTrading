import dataManipulator as dm
import logger
from backtesting import Backtest
import pandas_ta as ta
from multiprocessing import Pool, Manager, cpu_count
import json
import strategies

def runMasterBacktest(symbols, strategy):
    with open('config.json', 'r') as file:
        config = json.load(file)

    if config['plotResults'] and len(symbols) > 10:
        print("Too many symbols to plot results for.")

    # Create a multiprocessing manager and shared dictionary for strategies
    with Manager() as manager:
        # Shared dict that processes can safely update
        strategies = manager.dict({'dailyRange': 0, 'buyAndHold': 0, 'soloRSI': 0, 'rocTrendFollowingBull': 0, 'rocTrendFollowingBear': 0})

        # Use Pool to parallelize the backtest process
        with Pool(min(len(symbols), cpu_count())) as pool:
            # Run backtest in parallel and get the results
            if config['compareStrategies']:
                results = pool.starmap(runBacktestProcess, [(symbol, strategy) for symbol in symbols for strategy in strategies.keys()])

            elif config['findBest']:
                results = pool.starmap(findBestBacktest, [(symbol, strategies) for symbol in symbols])

            elif config['adaptiveStrategy']:
                results = pool.starmap(runAdaptiveBacktest, [(symbol, strategies) for symbol in symbols])

            else:
                results = pool.starmap(runBacktestProcess, [(symbol, strategy) for symbol in symbols])

        # After all backtests are done, log the aggregated results
        results = [result for result in results if result is not None]

        if config['sortResults']:
            results = sorted(results, key=lambda x: x[config['sortingCriteria']], reverse=True)

        for result in results:
            logger.logSimple(result)

        if config['findBest']:
            logger.compareResults(strategies)

        logger.logAggregatedResults(results)

def runBacktest(symbol, strategy, startPercent = 0, endPercent = 1, plot = False):
    df = dm.fetchData(symbol)
    
    if df is None:
        return None
    
    startIndex = int(startPercent * len(df))
    endIndex = int(endPercent * len(df))
    df = df.iloc[startIndex:endIndex]
    size = 0.75

    dm.createSignals(df, strategy)
    results = gatherBacktestResults(df, strategy, size, plot)
    
    if results is None:
        print(f"Backtest for {symbol} with strategy -{strategy}- failed or no trades were made.")
        return None

    return results

def runBacktestProcess(symbol, strategy):
    result = runBacktest(symbol, strategy)
    
    if result is None:
        return None
    
    # Convert result to a dictionary or other simple format
    simplifiedResult = dm.generateSimpleResult(symbol, strategy, result)

    return simplifiedResult

def findBestBacktest(symbol, strategies, startPercent = 0, endPercent = 1):
    bestStrategy = None
    bestResult = None
    bestSharpe = 0

    for strategy in strategies.keys():
        result = runBacktest(symbol, strategy, startPercent, endPercent)

        if result is None:
            return None
        
        if result['Sharpe Ratio'] > bestSharpe:
            bestResult = result
            bestSharpe = result['Sharpe Ratio']
            bestStrategy = strategy
    
    if bestStrategy is not None:
        strategies[bestStrategy] += 1

    else:
        return None

    simplifiedResult = dm.generateSimpleResult(symbol, bestStrategy, bestResult)

    return simplifiedResult

def runAdaptiveBacktest(symbol, strategies, startPercent = 0, endPercent = 0.5):
    strategy = findBestBacktest(symbol, strategies, startPercent, endPercent)['strategy']

    if strategy is None:
        return None
    
    result = runBacktest(symbol, strategy, endPercent, 1)
    simplifiedResult = dm.generateSimpleResult(symbol, strategy, result)

    return simplifiedResult

def gatherBacktestResults(df, strategy, size, plot):
    try:
        bt = Backtest(df, strategies.loadStrategy(strategy, df, size), cash=100000, margin=1/1, commission=0.0001)

    except Exception as e:
        print(f"Error running backtest: {e}")
        return None
        
    results = bt.run()

    if plot:
        bt.plot(resample=False)

    if results['# Trades'] == 0:
        return None
    
    return results