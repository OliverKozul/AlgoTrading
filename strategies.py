from backtesting import Strategy


def loadStrategy(strategy, df, size):
    class BuyAndHold(Strategy):
            def init(self):
                super().init()

            def next(self):
                super().next()

                if len(self.trades) == 0:
                    self.buy(size=size)

    class DailyRange(Strategy):
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

    class ROCBull(Strategy):
        maxPrice = -1
        stopLoss = -1
        atrCoef = 6

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
            
            if len(self.trades) > 0 and self.data.Close[-1] < self.stopLoss:
                for trade in self.trades:
                    trade.close()

    class ROCBear(Strategy):
        minPrice = int(1e9)
        stopLoss = -1
        atrCoef = 6

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

            if len(self.trades) > 0 and self.data.Close[-1] < self.minPrice:
                self.minPrice = self.data.Close[-1]
                self.stopLoss = self.data.Close[-1] + (self.atr[-1] * self.atrCoef)

            if len(self.trades) == 0 and self.BUYSignal > 0:
                buySize = size * (self.data.Close[-1] / (30 * self.atr[-1]))

                if buySize < 0.01:
                    buySize = 0.01

                elif buySize > 1:
                    buySize = 0.99

                self.sell(size=buySize)
                self.stopLoss = self.data.Close[-1] - (self.atr[-1] * self.atrCoef)
            
            elif len(self.trades) > 0 and self.data.Close[-1] > self.stopLoss:
                for trade in self.trades:
                    trade.close()

    class ROCMeanReversion(Strategy):
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
                buySize = size

                if buySize < 0.01:
                    buySize = 0.01

                elif buySize > 1:
                    buySize = 0.99

                tp = self.data.Close[-1] + self.atr[-1]
                sl = self.data.Close[-1] - self.atr[-1]

                if sl < 0:
                    sl = 0.01

                self.buy(size=buySize, tp=tp, sl=sl)
            
            if len(self.trades) > 0:
                for trade in self.trades:
                    if (self.data.index[-1]-trade.entry_time).days > 20:
                        trade.close()

    if strategy == 'buyAndHold':
            return BuyAndHold

    elif strategy == 'dailyRange':
        return DailyRange

    elif strategy == 'soloRSI':
        return SoloRSI

    elif strategy == 'rocTrendFollowingBull':
        return ROCBull

    elif strategy == 'rocTrendFollowingBear':
        return ROCBear
    
    elif strategy == 'rocMeanReversion':
        return ROCMeanReversion
