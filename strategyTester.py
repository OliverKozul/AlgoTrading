from backtesting import Strategy
from backtesting import Backtest
import re
import dataManipulator as dm

def runBacktest(symbol, strategy, startPercent = 0, endPercent = 1):
    df = dm.fetchData(symbol)
    startIndex = int(startPercent * len(df))
    endIndex = int(endPercent * len(df))
    df = df.iloc[startIndex:endIndex]
    size = 0.75

    if df is None:
        return None
    
    dm.createSignals(df, strategy)
    results = gatherBacktestResults(df, strategy, size)
    
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
    
    strategies[bestStrategy] += 1
    simplifiedResult = dm.generateSimpleResult(symbol, bestStrategy, bestResult)

    return simplifiedResult

def runAdaptiveBacktest(symbol, strategies, startPercent = 0, endPercent = 0.5):
    strategy = findBestBacktest(symbol, strategies, startPercent, endPercent)['strategy']

    if strategy is None:
        return None
    
    result = runBacktest(symbol, strategy, endPercent, 1)
    simplifiedResult = dm.generateSimpleResult(symbol, strategy, result)

    return simplifiedResult

def gatherBacktestResults(df, strategy, size):
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
            
            super().init()

            self.BUYSignal = self.I(SIGNALBUY)

        def next(self):
            super().next()

            if self.BUYSignal > 0:
                self.buy(size=size)
            
            elif len(self.trades) > 0 and self.data.Close[-1] > self.data.Open[-1]:
                for trade in self.trades:
                    trade.close()

    class SoloRSI(Strategy):
        def init(self):
            def SIGNALBUY():
                return df.BUYSignal
            
            super().init()

            self.BUYSignal = self.I(SIGNALBUY)

        def next(self):
            super().next()

            if self.BUYSignal > 0:
                self.buy(size=size)
            
            elif len(self.trades) > 0 and self.data.Close[-1] > self.data.Open[-1]:
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

    except Exception as e:
        print(f"Error running backtest: {e}")
        return None
        
    results = bt.run()
    return results