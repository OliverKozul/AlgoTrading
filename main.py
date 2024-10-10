import logger
import strategyTester as st
import dataManipulator as dm
from multiprocessing import Pool, Manager
import pandas as pd


if __name__ == "__main__":
    findBest = True
    compareStrategies = False
    adaptiveStrategy = False
    symbols = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
    # symbols = ['AMD', 'NVDA', 'CAT']
    # symbols = ['AMD', 'NVDA', 'COST']
    strategy = 'dailyRange'

    # Create a multiprocessing manager and shared dictionary for strategies
    with Manager() as manager:
        # Shared dict that processes can safely update
        strategies = manager.dict({'dailyRange': 0, 'buyAndHold': 0, 'soloRSI': 0})

        # Use Pool to parallelize the backtest process
        with Pool() as pool:
            # Run backtest in parallel and get the results
            if compareStrategies:
                results = pool.starmap(st.runBacktestProcess, [(symbol, strategy) for symbol in symbols for strategy in strategies.keys()])

            elif findBest:
                results = pool.starmap(st.findBestBacktest, [(symbol, strategies) for symbol in symbols])

            elif adaptiveStrategy:
                results = pool.starmap(st.runAdaptiveBacktest, [(symbol, strategies) for symbol in symbols])

            else:
                results = pool.starmap(st.runBacktestProcess, [(symbol, strategy) for symbol in symbols])

        # After all backtests are done, log the aggregated results
        for result in results:
            logger.logSimple(result)

        if findBest:
            logger.compareResults(strategies)

        logger.logAggregatedResults(results)
        