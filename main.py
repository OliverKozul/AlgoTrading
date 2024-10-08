import logger
import strategyTester as st
import dataManipulator as dm
from multiprocessing import Pool, Manager
import pandas as pd

def runBacktestProcess(symbol, strategy, strategies, findBest):
    bestStrategy = strategy

    if findBest:
        bestSharpe = 0
        

        for strategy in strategies.keys():
            result = st.runBacktest(symbol, strategy)

            if result is None:
                return None
            
            if result['Sharpe Ratio'] > bestSharpe:
                bestSharpe = result['Sharpe Ratio']
                bestStrategy = strategy
        
        strategies[bestStrategy] += 1

    else:
        result = st.runBacktest(symbol, strategy)
    
    if result is None:
        return None
    
    # Convert result to a dictionary or other simple format
    simplifiedResult = {
        'symbol': symbol,
        'maxDrawdown': result['Max. Drawdown [%]'],
        'return': result['Return [%]'],
        'sharpe': result['Sharpe Ratio'],
        'equity_curve': result['_equity_curve'],
        'strategy': bestStrategy
    }

    return simplifiedResult

if __name__ == "__main__":
    findBest = False
    compareStrategies = False
    # symbols = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
    symbols = ['AMD', 'NVDA', 'CAT', 'AAPL', 'MSFT', 'GOOG', 'AMZN', 'CSCO', 'QCOM', 'IBM', 'NFLX', 'T']
    strategy = 'dailyRange'

    # Create a multiprocessing manager and shared dictionary for strategies
    with Manager() as manager:
        # Shared dict that processes can safely update
        strategies = manager.dict({'dailyRange': 0, 'buyAndHold': 0})

        # Use Pool to parallelize the backtest process
        with Pool() as pool:
            # Run backtest in parallel and get the results
            if compareStrategies and not findBest:
                results = pool.starmap(runBacktestProcess, [(symbol, strategy, strategies, findBest) for symbol in symbols for strategy in strategies.keys()])

            else:
                results = pool.starmap(runBacktestProcess, [(symbol, strategy, strategies, findBest) for symbol in symbols])

        # After all backtests are done, log the aggregated results
        for result in results:
            logger.logSimple(result)

        if findBest:
            logger.compareResults(strategies)

        logger.logAggregatedResults(results)
        