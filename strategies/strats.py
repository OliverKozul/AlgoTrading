from backtesting import Strategy

dataframe = None
tradeSize = 0

# Strategy loader function
def loadStrategy(strategy, df, size):
    strategies = {
        'buyAndHold': BuyAndHold,
        'dailyRange': DailyRange,
        'soloRSI': SoloRSI,
        'rocTrendFollowingBull': ROCBull,
        'rocTrendFollowingBear': ROCBear,
        'rocMeanReversion': ROCMeanReversion
    }

    if strategy not in strategies:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    global dataframe
    global tradeSize
    dataframe = df
    tradeSize = size

    return strategies[strategy]

# Base class for strategies that use ATR and BUYSignal
class BaseStrategy(Strategy):
    def init(self):
        super().init()

        def SIGNALBUY():
            return self.df.BUYSignal

        def ATR():
            return self.df.atr

        global dataframe
        global tradeSize
        self.df = dataframe
        self.size = tradeSize
        self.BUYSignal = self.I(SIGNALBUY)
        self.atr = self.I(ATR)
        self.tpCoef = 2
        self.slCoef = 2

    def next(self):
        if len(self.trades) == 0 and self.BUYSignal > 0:
            buySize = self.calculateBuySize()
            self.buy(size=buySize)

    def nextWithTPSL(self):
        if len(self.trades) == 0 and self.BUYSignal > 0:
            buySize = self.calculateBuySize()
            tp = self.data.Close[-1] + self.tpCoef * self.atr[-1]
            sl = max(0.01, self.data.Close[-1] - self.slCoef * self.atr[-1])
            self.buy(size=buySize, tp=tp, sl=sl)

    def closeNextGreenDay(self):
        if len(self.trades) > 0 and self.data.Close[-1] > self.data.Open[-1]:
            for trade in self.trades:
                trade.close()

    def calculateBuySize(self):
        buySize = self.size * (self.data.Close[-1] / (30 * self.atr[-1]))
        return max(0.01, min(buySize, 0.99))
    
class TrailingStopLossStrategy(BaseStrategy):
    def init(self):
        super().init()
        self.stopLoss = -1
        self.maxPrice = -1
        self.minPrice = float('inf')
        self.atrCoef = 6  # Can be customized in child classes

    def updateTrailingStop(self):
        if len(self.trades) > 0:
            trade = self.trades[0]
            
            if trade.is_long:  # Long position trailing stop
                if self.data.Close[-1] > self.maxPrice:
                    self.maxPrice = self.data.Close[-1]
                    self.stopLoss = self.data.Close[-1] - (self.atr[-1] * self.atrCoef)

            elif trade.is_short:  # Short position trailing stop
                if self.data.Close[-1] < self.minPrice:
                    self.minPrice = self.data.Close[-1]
                    self.stopLoss = self.data.Close[-1] + (self.atr[-1] * self.atrCoef)

    def closeTradesIfNeeded(self):
        for trade in self.trades:
            # Close long trades if price drops below the stop loss
            if trade.is_long and self.data.Close[-1] < self.stopLoss:
                trade.close()

            # Close short trades if price rises above the stop loss
            elif trade.is_short and self.data.Close[-1] > self.stopLoss:
                trade.close()

    def next(self):
        super().next()
        self.updateTrailingStop()
        self.closeTradesIfNeeded()


# Buy and Hold strategy
class BuyAndHold(BaseStrategy):
    def next(self):
        if len(self.trades) == 0:
            self.buy(size=self.size)

# Daily Range strategy
class DailyRange(BaseStrategy):
    def next(self):
        super().closeNextGreenDay()
        super().next()

# Solo RSI strategy
class SoloRSI(BaseStrategy):
    def next(self):
        super().closeNextGreenDay()
        super().next()

# ROC Trend Following Bull strategy
class ROCBull(TrailingStopLossStrategy):
    def init(self):
        super().init()
        self.atrCoef = 6

    def next(self):
        super().next()

# ROC Trend Following Bear strategy
class ROCBear(TrailingStopLossStrategy):
    def init(self):
        super().init()
        self.atrCoef = 6

    def next(self):
        super().next()
        

# ROC Mean Reversion strategy
class ROCMeanReversion(BaseStrategy):
    def init(self):
        super().init()
        self.tpCoef = 1
        self.slCoef = 1

    def next(self):
        super().nextWithTPSL()
