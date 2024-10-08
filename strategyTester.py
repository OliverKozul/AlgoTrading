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
    class BuyAndHold(Strategy):
        def init(self):
            super().init()

        def next(self):
            super().next()

            if len(self.trades) == 0:
                self.buy(size=0.2)

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
        mysize = 0.1

        def init(self):
            def SIGNALBUY():
                return df.BUYSignal
            
            super().init()

            self.BUYSignal = self.I(SIGNALBUY)

        def next(self):
            super().next()

            if self.BUYSignal > 0:
                self.buy(size=self.mysize)
            
            elif len(self.trades) > 0:
                for trade in self.trades:
                    trade.close()

    try:
        if strategy == 'buyAndHold':
            bt = Backtest(df, BuyAndHold, cash=100000, margin=1/15, commission=0.000)

        elif strategy == 'dailyRangeH':
            bt = Backtest(df, DailyRangeH, cash=100000, margin=1/15, commission=0.000)

        elif strategy == 'dailyRange':
            bt = Backtest(df, DailyRange, cash=100000, margin=1/15, commission=0.000)

    except Exception as e:
        print(f"Error running backtest: {e}")
        return None
        
    results = bt.run()
    return results