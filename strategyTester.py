from backtesting import Strategy
from backtesting import Backtest
import re
import dataManipulator as dm

def runBacktest(symbol, strategy):
    df = dm.fetchData(symbol)

    if df is None:
        return None
    
    dm.createSignals(df, strategy)
    df.set_index('Date', inplace=True)
    results = gatherBacktestResults(df, strategy)
    
    return results

def gatherBacktestResults(df, strategy):
    class DailyRange(Strategy):
        mysize = 0.075
        pospow = 0.75
        lastBuy = -1
        tp1 = 1.025
        sl1 = 0.98
        maxTrades = 3
        bahdd = 0
        maxPrice = 0
        closeSize = 0.2

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

            if self.data.Close[-1] > self.maxPrice:
                self.maxPrice = self.data.Close[-1]

            if 100 * (1 - self.data.Close[-1] / self.maxPrice) > self.bahdd:
                self.bahdd = 100 * (1 - self.data.Close[-1] / self.maxPrice)
        
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

    class BuyAndHold(Strategy):
        def init(self):
            super().init()

        def next(self):
            super().next()

            if len(self.trades) == 0:
                self.buy(size=0.2)

    try:
        if strategy == 'dailyRange':
            bt = Backtest(df, DailyRange, cash=100000, margin=1/15, commission=0.000)

        elif strategy == 'buyAndHold':
            bt = Backtest(df, BuyAndHold, cash=100000, margin=1/15, commission=0.000)

    except Exception as e:
        print(f"Error running backtest: {e}")
        return None
        
    results = bt.run()
    return results