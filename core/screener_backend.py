import yfinance as yf
import datetime as dt

class Stock:
    def __init__(self, ticker, date):
        self.ticker = ticker
        self.date = date
        self.stock = yf.Ticker(ticker)
        self.historical_prices = self.stock.history(start=date)
        self.eps_ttms = self.stock.info['trailingEps']
        self.ttm_change = round(self.stock.info['52WeekChange'], 2)
        self.price = self.historical_prices['Close'].iloc[0]
        self.next_year_change = self.calculate_change(365)
        self.pe_ratio = round(self.price / self.eps_ttms, 2)

    def calculate_change(self, timedelta_days):
        # future_price = 0
        # print(timedelta_days)
        future_price = self.stock.history(start=self.date + dt.timedelta(days=timedelta_days))['Close'].iloc[0]
        return round((future_price - self.price) / self.price, 2)    

    def __str__(self):
        return f'{self.ticker} P/E Ratio: {self.pe_ratio}, TTM Change: {self.ttm_change}, Next Year Change: {self.next_year_change}'

    def __repr__(self):
        return f'{self.ticker} P/E Ratio: {self.pe_ratio}, TTM Change: {self.ttm_change}, Next Year Change: {self.next_year_change}'


class Portfolio:
    def __init__(self, tickers, date):
        self.stocks = [Stock(ticker, date) for ticker in tickers]

    def filter(self, variable, threshold, operator):
        if operator == '>':
            self.stocks = [stock for stock in self.stocks if getattr(stock, variable) > threshold]
        elif operator == '<':
            self.stocks = [stock for stock in self.stocks if getattr(stock, variable) < threshold]
        elif operator == '==':
            self.stocks = [stock for stock in self.stocks if getattr(stock, variable) == threshold]
        else:
            print(f"Invalid operator: {operator}")

    def __str__(self):
        return '\n'.join([str(stock) for stock in self.stocks])

    def __repr__(self):
        return '\n'.join([str(stock) for stock in self.stocks])

# tickers = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'AMD']
# tickers.sort()

# date = dt.datetime(2024, 1, 1)

# portfolio = Portfolio(tickers, date)
# portfolio.filter('pe_ratio', 10, '>')

# print(portfolio)
