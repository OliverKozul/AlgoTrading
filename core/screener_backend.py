import yfinance as yf
import datetime as dt

class Stock:
    def __init__(self, ticker, date):
        self.ticker = ticker
        self.date = date
        self.stock = yf.Ticker(ticker)
        self.historical_prices = self.stock.history(start=date) if self.stock.history(start=date).shape[0] > 0 else 'N/A'
        self.eps_ttm = self.stock.info['trailingEps'] if 'trailingEps' in self.stock.info else 'N/A'
        self.ttm_change = round(self.stock.info['52WeekChange'], 2) if '52WeekChange' in self.stock.info else 'N/A'
        self.has_complete_data = self.eps_ttm != 'N/A' and self.ttm_change != 'N/A' and type(self.historical_prices) != str
        self.price = self.historical_prices['Close'].iloc[0] if self.has_complete_data else 'N/A'
        self.next_year_change = self.calculate_change(365) if self.has_complete_data else 'N/A'
        self.pe_ratio = round(self.price / self.eps_ttm, 2) if self.has_complete_data else 'N/A'

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
            self.stocks = [stock for stock in self.stocks if stock.has_complete_data and getattr(stock, variable) > threshold]
        elif operator == '<':
            self.stocks = [stock for stock in self.stocks if stock.has_complete_data and getattr(stock, variable) < threshold]
        elif operator == '==':
            self.stocks = [stock for stock in self.stocks if stock.has_complete_data and getattr(stock, variable) == threshold]
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
