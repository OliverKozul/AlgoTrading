from typing import Type
from pandas import DataFrame
from backtesting import Strategy
import strategies.strategy_tester as st
import strategies.strats as strats


dataframe: DataFrame = None
trade_size: float = 0

# Strategy loader function
def load_strategy(strategy: str, df: DataFrame, size: float) -> Type[Strategy]:
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
    def init(self) -> None:
        super().init()

        def SIGNALBUY() -> float:
            return self.df.BUYSignal

        def ATR() -> float:
            return self.df.atr

        global dataframe
        global trade_size
        self.df = dataframe
        self.size = trade_size
        self.BUYSignal = self.I(SIGNALBUY)
        self.atr = self.I(ATR)
        self.tp_coef = 2
        self.sl_coef = 2

    def next(self) -> None:
        if len(self.trades) == 0 and self.BUYSignal > 0:
            trade_size = self.calculate_trade_size()

            if self.BUYSignal == 1:
                self.buy(size=trade_size)
            elif self.BUYSignal == 2:
                self.sell(size=trade_size)

    def next_with_tpsl(self) -> None:
        if len(self.trades) == 0 and self.BUYSignal > 0:
            trade_size = self.calculate_trade_size()
            if self.BUYSignal == 1:
                tp = self.data.Close[-1] + self.tp_coef * self.atr[-1]
                sl = max(0.01, self.data.Close[-1] - self.sl_coef * self.atr[-1])
                self.buy(size=trade_size, tp=tp, sl=sl)
            elif self.BUYSignal == 2:
                tp = self.data.Close[-1] - self.tp_coef * self.atr[-1]
                sl = max(0.01, self.data.Close[-1] + self.sl_coef * self.atr[-1])
                self.sell(size=trade_size, tp=tp, sl=sl)

    def close_next_green_day(self) -> None:
        if len(self.trades) > 0 and self.data.Close[-1] > self.data.Open[-1]:
            for trade in self.trades:
                if trade.is_long:
                    trade.close()

    def close_next_red_day(self) -> None:
        if len(self.trades) > 0 and self.data.Close[-1] < self.data.Open[-1]:
            for trade in self.trades:
                if trade.is_short:
                    trade.close()

    def calculate_trade_size(self) -> float:
        trade_size = self.size * (self.data.Close[-1] / (self.atr[-1] ** 2))
        return max(0.01, min(trade_size, 0.99))
    
class Trailing_Stop_Loss_Strategy(Base_Strategy):
    def init(self) -> None:
        super().init()
        self.stop_loss = -1
        self.max_price = -1
        self.min_price = float('inf')
        self.atr_coef = 6  # Can be customized in child classes

    def update_trailing_stop(self) -> None:
        if len(self.trades) > 0:
            trade = self.trades[0]
            
            if trade.is_long:
                if self.data.Close[-1] > self.max_price:
                    self.max_price = self.data.Close[-1]
                    self.stop_loss = self.data.Close[-1] - (self.atr[-1] * self.atr_coef)

            elif trade.is_short:
                if self.data.Close[-1] < self.min_price:
                    self.min_price = self.data.Close[-1]
                    self.stop_loss = self.data.Close[-1] + (self.atr[-1] * self.atr_coef)

    def close_trades_if_needed(self) -> None:
        for trade in self.trades:
            if trade.is_long and self.data.Close[-1] < self.stop_loss:
                trade.close()
            elif trade.is_short and self.data.Close[-1] > self.stop_loss:
                trade.close()

    def next(self) -> None:
        super().next()
        self.update_trailing_stop()
        self.close_trades_if_needed()


# Buy and Hold strategy
class Buy_And_Hold(Base_Strategy):
    def next(self) -> None:
        if len(self.trades) == 0:
            self.buy(size=self.size)

# Daily Range strategy
class Daily_Range(Base_Strategy):
    def next(self) -> None:
        super().close_next_green_day()
        super().next()

# Solo RSI strategy
class Solo_RSI(Base_Strategy):
    def next(self) -> None:
        super().close_next_green_day()
        super().next()

# ROC Trend Following Bull strategy
class ROC_Trend_Following_Bull(Trailing_Stop_Loss_Strategy):
    def init(self) -> None:
        super().init()
        self.atr_coef = 6

    def next(self) -> None:
        super().next()

# ROC Trend Following Bear strategy
class ROC_Trend_Following_Bear(Trailing_Stop_Loss_Strategy):
    def init(self) -> None:
        super().init()
        self.atr_coef = 6

    def next(self) -> None:
        super().next()

# ROC Mean Reversion strategy
class ROC_Mean_Reversion(Base_Strategy):
    def init(self) -> None:
        super().init()

    def next(self) -> None:
        super().close_next_green_day()
        super().next()

# Buy And Holder strategy
class Buy_And_Holder(Base_Strategy):
    def init(self) -> None:
        super().init()
        self.atr_coef = 6

    def next(self) -> None:
        super().next()

# Buy After Red Day strategy
class Buy_After_Red_Day(Base_Strategy):
    def next(self) -> None:
        super().close_next_green_day()
        super().next()

# Buy After Green Day strategy
class Buy_After_Green_Day(Base_Strategy):
    def next(self) -> None:
        super().close_next_green_day()
        super().next()

# Shorting RSI strategy
class Shorting_RSI(Base_Strategy):
    def next(self) -> None:
        super().close_next_red_day()
        super().next()

# Combination strategy
class Combination(Base_Strategy):
    def next(self) -> None:
        super().close_next_green_day()
        super().close_next_red_day()
        super().next()
        