from backtesting import Strategy
import strategies.strategy_tester as st
import strategies.strats as strats

dataframe = None
trade_size = 0

# Strategy loader function
def load_strategy(strategy, df, size):
    strategies = st.load_strategies_from_json('strategies\strategies.json')
    community_strategies = st.load_strategies_from_json('strategies\community_strategies.json')
    strategies.update(community_strategies)
    keys = strategies.keys()
    strategies = {key: getattr(strats, key) for key in keys}

    if strategy not in strategies:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    global dataframe
    global trade_size
    dataframe = df
    trade_size = size

    return strategies[strategy]

# Base class for strategies that use ATR and BUYSignal
class Base_Strategy(Strategy):
    def init(self):
        super().init()

        def SIGNALBUY():
            return self.df.BUYSignal

        def ATR():
            return self.df.atr

        global dataframe
        global trade_size
        self.df = dataframe
        self.size = trade_size
        self.BUYSignal = self.I(SIGNALBUY)
        self.atr = self.I(ATR)
        self.tp_coef = 2
        self.sl_coef = 2

    def next(self):
        if len(self.trades) == 0 and self.BUYSignal > 0:
            buySize = self.calculate_buy_size()
            self.buy(size=buySize)

    def next_with_tpsl(self):
        if len(self.trades) == 0 and self.BUYSignal > 0:
            buySize = self.calculate_buy_size()
            tp = self.data.Close[-1] + self.tp_coef * self.atr[-1]
            sl = max(0.01, self.data.Close[-1] - self.sl_coef * self.atr[-1])
            self.buy(size=buySize, tp=tp, sl=sl)

    def close_next_green_day(self):
        if len(self.trades) > 0 and self.data.Close[-1] > self.data.Open[-1]:
            for trade in self.trades:
                trade.close()

    def calculate_buy_size(self):
        buySize = self.size * (self.data.Close[-1] / (30 * self.atr[-1]))
        return max(0.01, min(buySize, 0.99))
    
class Trailing_Stop_Loss_Strategy(Base_Strategy):
    def init(self):
        super().init()
        self.stop_loss = -1
        self.max_price = -1
        self.min_price = float('inf')
        self.atr_coef = 6  # Can be customized in child classes

    def update_trailing_stop(self):
        if len(self.trades) > 0:
            trade = self.trades[0]
            
            if trade.is_long:  # Long position trailing stop
                if self.data.Close[-1] > self.max_price:
                    self.max_price = self.data.Close[-1]
                    self.stop_loss = self.data.Close[-1] - (self.atr[-1] * self.atr_coef)

            elif trade.is_short:  # Short position trailing stop
                if self.data.Close[-1] < self.min_price:
                    self.min_price = self.data.Close[-1]
                    self.stop_loss = self.data.Close[-1] + (self.atr[-1] * self.atr_coef)

    def close_trades_if_needed(self):
        for trade in self.trades:
            # Close long trades if price drops below the stop loss
            if trade.is_long and self.data.Close[-1] < self.stop_loss:
                trade.close()

            # Close short trades if price rises above the stop loss
            elif trade.is_short and self.data.Close[-1] > self.stop_loss:
                trade.close()

    def next(self):
        super().next()
        self.update_trailing_stop()
        self.close_trades_if_needed()


# Buy and Hold strategy
class Buy_And_Hold(Base_Strategy):
    def next(self):
        if len(self.trades) == 0:
            self.buy(size=self.size)

# Daily Range strategy
class Daily_Range(Base_Strategy):
    def next(self):
        super().close_next_green_day()
        super().next()

# Solo RSI strategy
class Solo_RSI(Base_Strategy):
    def next(self):
        super().close_next_green_day()
        super().next()

# ROC Trend Following Bull strategy
class ROC_Trend_Following_Bull(Trailing_Stop_Loss_Strategy):
    def init(self):
        super().init()
        self.atr_coef = 6

    def next(self):
        super().next()

# ROC Trend Following Bear strategy
class ROC_Trend_Following_Bear(Trailing_Stop_Loss_Strategy):
    def init(self):
        super().init()
        self.atr_coef = 6

    def next(self):
        super().next()
        

# ROC Mean Reversion strategy
class ROC_Mean_Reversion(Base_Strategy):
    def init(self):
        super().init()
        self.tp_coef = 1
        self.sl_coef = 1

    def next(self):
        super().next_with_tpsl()

class Buy_And_Hold_2(Base_Strategy):
    def init(self):
        super().init()
        
    def next(self):
        if len(self.trades) == 0:
            self.buy(size=self.size)

class Buy_And_Holder(Base_Strategy):
    def init(self):
        super().init()
        self.atr_coef = 6

    def next(self):
        super().next()

class Buy_After_Red_Day(Base_Strategy):
    def next(self):
        super().close_next_green_day()
        super().next()