import dataManipulator as dm
import logger
from backtesting import Strategy
from backtesting import Backtest
import pandas_ta as ta
from multiprocessing import Pool, Manager
import json


def runMasterBacktest(symbols, strategy):
    with open('config.json', 'r') as file:
        config = json.load(file)

    if config['plotResults'] and len(symbols) > 10:
        print("Too many symbols to plot results for.")

    # Create a multiprocessing manager and shared dictionary for strategies
    with Manager() as manager:
        # Shared dict that processes can safely update
        strategies = manager.dict({'dailyRange': 0, 'buyAndHold': 0, 'soloRSI': 0, 'rocTrendFollowing': 0})

        # Use Pool to parallelize the backtest process
        with Pool() as pool:
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
    class BuyAndHold(Strategy):
        def init(self):
            super().init()

        def next(self):
            super().next()

            if len(self.trades) == 0:
                self.buy(size=size)

    class DailyRangeH(Strategy):
        mysize = 0.075
        pospow = 0.75
        lastBuy = -1
        tp1 = 1.025
        sl1 = 0.98
        maxTrades = 3

        def init(self):
            def SIGNALBUY():
                return df.BUYSignal

            def SIGNALSELL():
                return df.SELLSignal
            
            def BBWidth():
                return df.width
            
            super().init()

            self.BUYSignal = self.I(SIGNALBUY)
            self.SELLSignal = self.I(SIGNALSELL)
            self.bbwidth = self.I(BBWidth)

        def next(self):
            super().next()

            if self.BUYSignal > 0 and self.lastBuy != self.data.index[-1].day and len(self.trades) < self.maxTrades:
                widthPercent = self.bbwidth[-1]

                if widthPercent < 0:
                    widthPercent = -widthPercent

                widthPercent = min(1 / widthPercent, 2)
                size = self.mysize * widthPercent * self.pospow
                self.lastBuy = self.data.index[-1].day
                
                if size < 0.01:
                    size = 0.01

                if size < 1:
                    self.buy(size=size, sl=self.data.Close[-1] * self.sl1, tp=self.data.Close[-1] * self.tp1)
            
            if len(self.trades) > 0 and self.SELLSignal > 0:
                for trade in self.trades:
                    trade.close()

    class DailyRange(Strategy):
        def init(self):
            def SIGNALBUY():
                return df.BUYSignal
            
            def ATR():
                return ta.atr(df.High, df.Low, df.Close, length=14)
            
            super().init()

            self.BUYSignal = self.I(SIGNALBUY)
            self.atr = self.I(ATR)

        def next(self):
            super().next()

            if len(self.trades) == 0 and self.BUYSignal > 0:
                # buySize = size * (self.data.Close[-1] / (30 * self.atr[-1]))

                # if buySize < 0.01:
                #     buySize = 0.01

                # elif buySize > 1:
                #     buySize = 0.99

                self.buy(size=size)
            
            elif len(self.trades) > 0 and self.data.Close[-1] > self.data.Open[-1]:
                for trade in self.trades:
                    trade.close()

    class SoloRSI(Strategy):
        def init(self):
            def SIGNALBUY():
                return df.BUYSignal
            
            def ATR():
                return df.atr
            
            super().init()

            self.BUYSignal = self.I(SIGNALBUY)
            self.atr = self.I(ATR)

        def next(self):
            super().next()

            if len(self.trades) == 0 and self.BUYSignal > 0:
                buySize = size * (self.data.Close[-1] / (30 * self.atr[-1]))

                if buySize < 0.01:
                    buySize = 0.01

                elif buySize > 1:
                    buySize = 0.99

                self.buy(size=buySize)
            
            elif len(self.trades) > 0 and self.data.Close[-1] > self.data.Open[-1]:
                for trade in self.trades:
                    trade.close()

    class ROC(Strategy):
        maxPrice = -1
        stopLoss = -1
        atrCoef = 3

        def init(self):
            def SIGNALBUY():
                return df.BUYSignal
            
            def ATR():
                return df.atr
            
            super().init()

            self.BUYSignal = self.I(SIGNALBUY)
            self.atr = self.I(ATR)

        def next(self):
            super().next()

            if len(self.trades) > 0 and self.data.Close[-1] > self.maxPrice:
                self.maxPrice = self.data.Close[-1]
                self.stopLoss = self.data.Close[-1] - (self.atr[-1] * self.atrCoef)

            if len(self.trades) == 0 and self.BUYSignal > 0:
                buySize = size * (self.data.Close[-1] / (30 * self.atr[-1]))

                if buySize < 0.01:
                    buySize = 0.01

                elif buySize > 1:
                    buySize = 0.99

                self.buy(size=buySize)
                self.stopLoss = self.data.Close[-1] - (self.atr[-1] * self.atrCoef)
            
            elif len(self.trades) > 0 and self.data.Close[-1] < self.stopLoss:
                for trade in self.trades:
                    trade.close()

    try:
        if strategy == 'buyAndHold':
            bt = Backtest(df, BuyAndHold, cash=100000, margin=1/1, commission=0.0001)

        elif strategy == 'dailyRangeH':
            bt = Backtest(df, DailyRangeH, cash=100000, margin=1/1, commission=0.0001)

        elif strategy == 'dailyRange':
            bt = Backtest(df, DailyRange, cash=100000, margin=1/1, commission=0.0001)

        elif strategy == 'soloRSI':
            bt = Backtest(df, SoloRSI, cash=100000, margin=1/1, commission=0.0001)

        elif strategy == 'rocTrendFollowing':
            bt = Backtest(df, ROC, cash=100000, margin=1/1, commission=0.0001)

    except Exception as e:
        print(f"Error running backtest: {e}")
        return None
        
    results = bt.run()

    if plot:
        bt.plot(resample=False)

    if results['# Trades'] == 0:
        return None
    
    return results