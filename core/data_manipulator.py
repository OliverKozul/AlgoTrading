import yfinance as yf
import pandas as pd
import pandas_ta as ta
import re
from strategies.strategy_tester import load_strategies_from_json


def fetch_data(symbol, startDate = None, endDate = None):
    try:
        df = yf.download(symbol, start=startDate, end=endDate, period='5y', interval='1d', progress=False)
        
        if df.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        
        df = df.reset_index()
        df.drop(columns=['Adj Close', 'Volume'], inplace=True)
        df.dropna(inplace=True)
        
        return df

    except Exception as e:
        print(f"Error fetching data for symbol {symbol}: {e}")
        return None

def fetch_data_multiple(symbols, startDate = None, endDate = None):
    try:
        dfs = yf.download(symbols, start=startDate, end=endDate, period='5y', interval='1d', progress=False)

        if dfs.empty:
            raise ValueError("No data found for given symbols")

        dfs.drop(columns=['Adj Close', 'Volume'], inplace=True)
        return dfs

    except Exception as e:
        print(f"Error fetching data for symbols: {e}")
        return None

def load_symbols(category):
    if category == 'SP':
        return pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist() + ['SPY']
    
    elif category == 'R2000':
        return pd.read_csv('data/R2000.csv').iloc[:, 0].tolist()

    elif category == 'futures':
        return ['ES=F', 'YM=F', 'NQ=F', 'RTY=F', 'CL=F', 'GC=F', 'SI=F', 'HG=F', 'PL=F', 'PA=F', 'NG=F', 'ZB=F', 'ZT=F', 'ZN=F', 'ZS=F', 'ZW=F', 'ZC=F', 'ZL=F', 'ZM=F']
    
    else:
        print("Invalid index specified.")
        return None

def camel_case_to_name(camel_case_str):
    # Add a space before each capital letter and capitalize the first letter of the string
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', camel_case_str).title()

def snake_case_to_name(snake_case_str):
    # Replace underscores with spaces and capitalize the first letter of the string
    return snake_case_str.replace('_', ' ')

def clean_stock_data(stock_data, symbols):
    for symbol, data in stock_data.items():
        if data is None:
            stock_data.pop(symbol)
            symbols.remove(symbol)

    max_length = max(len(data) for data in stock_data.values())

    if any(len(data) != max_length for data in stock_data.values()):
        print(f"Data length mismatch. Removing all stocks that are not of length: {max_length}.")
        
    else:
        print(f"All data lengths are equal length: {max_length}.")

    for symbol, data in stock_data.items():
        if len(data) != max_length:
            stock_data.pop(symbol)
            symbols.remove(symbol)

    return stock_data

def generate_simple_result(symbol, strategy, result):
    simplified_result = {
        'symbol': symbol,
        'max_drawdown': result['Max. Drawdown [%]'],
        'return': result['Return [%]'],
        'sharpe': result['Sharpe Ratio'],
        '# trades': result['# Trades'],
        'avg_trade_duration': result['Avg. Trade Duration'],
        'equity_curve': result['_equity_curve'],
        'strategy': strategy
    }

    return simplified_result

def calculate_n_day_returns(df, n):
    df.loc[df['BUYSignal'] == 1, f'{n}_day_return'] = df['Close'].shift(-n-1).pct_change(fill_method=None) * 100
    average_return = df.loc[df['BUYSignal'] == 1, f'{n}_day_return'].mean()
    df.drop(columns=[f'{n}_day_return'], inplace=True)

    return average_return

def create_signals(df, strategy):
    df['BUYSignal'] = 0

    signal_functions = load_strategies_from_json('strategies\strategies.json')
    signal_functions.update(load_strategies_from_json('strategies\community_strategies.json'))

    for key in signal_functions:
        strategy_name_words = key.split('_')
        strategy_name = ''.join([word.lower() + "_" for word in strategy_name_words])
        function_name = f"create_{strategy_name}signals"
        signal_functions[key] = globals().get(function_name)

    signal_functions.get(strategy, lambda x: None)(df)
    df.set_index('Date', inplace=True)
    return df[-1000:] # !!! This is a temporary fix to avoid issues with the non-aligned data

def create_buy_and_hold_signals(df):
    df['BUYSignal'] = 1
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

# Daily Range

def create_daily_range_signals(df):
    add_daily_range_columns(df)
    create_daily_range_buy_signals(df)
    remove_daily_range_columns(df)

def add_daily_range_columns(df):
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df['current_percent'] = 100 * (df['Close'] - df['Low']) / (df['High'] - df['Low'])
    df.dropna(inplace=True)

def create_daily_range_buy_signals(df, low_percentage=10):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'current_percent']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'current_percent' columns."
    
    # Create the condition for buy signals
    buy_signal_condition = (df['current_percent'] <= low_percentage)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buy_signal_condition, 'BUYSignal'] = 1

def remove_daily_range_columns(df):
    df.drop(columns=['current_percent'], inplace=True)

# Solo RSI

def create_solo_rsi_signals(df):
    add_solo_rsi_columns(df)
    create_solo_rsi_buy_signals(df)
    remove_solo_rsi_columns(df)

def add_solo_rsi_columns(df, rsi_period=2):
    df['rsi'] = ta.rsi(df['Close'], length=rsi_period)
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

def create_solo_rsi_buy_signals(df, rsi_threshold=10):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'rsi']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'rsi' columns."

    # Create the condition for buy signals
    buy_signal_condition = (df['rsi'] < rsi_threshold)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buy_signal_condition, 'BUYSignal'] = 1

def remove_solo_rsi_columns(df):
    df.drop(columns=['rsi'], inplace=True)

# ROC trend_following Bull

def create_roc_trend_following_bull_signals(df):
    add_roc_trend_following_bull_columns(df)
    create_roc_trend_following_bull_buy_signals(df)
    remove_roc_trend_following_bull_columns(df)

def add_roc_trend_following_bull_columns(df, rocPeriod = 60):
    df['roc'] = ta.roc(df['Close'], length=rocPeriod)
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

def create_roc_trend_following_bull_buy_signals(df, rocThreshold = 30):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'roc']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'roc' columns."
    
    # Create the condition for buy signals
    buy_signal_condition = (df['roc'] > rocThreshold)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buy_signal_condition, 'BUYSignal'] = 1

def remove_roc_trend_following_bull_columns(df):
    df.drop(columns=['roc'], inplace=True)

# ROC trend_following Bear

def create_roc_trend_following_bear_signals(df):
    add_roc_trend_following_bear_columns(df)
    create_roc_trend_following_bear_buy_signals(df)
    remove_roc_trend_following_bear_columns(df)

def add_roc_trend_following_bear_columns(df, rocPeriod = 60):
    df['roc'] = ta.roc(df['Close'], length=rocPeriod)
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

def create_roc_trend_following_bear_buy_signals(df, rocThreshold = -30):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'roc']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'roc' columns."
    
    # Create the condition for buy signals
    buy_signal_condition = (df['roc'] < rocThreshold)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buy_signal_condition, 'BUYSignal'] = 1

def remove_roc_trend_following_bear_columns(df):
    df.drop(columns=['roc'], inplace=True)

# ROC Mean Reversion

def create_roc_mean_reversion_signals(df):
    add_roc_mean_reversion_columns(df)
    create_roc_mean_reversion_buy_signals(df)
    remove_roc_mean_reversion_columns(df)

def add_roc_mean_reversion_columns(df, rocPeriod = 14):
    df['roc'] = ta.roc(df['Close'], length=rocPeriod)
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

def create_roc_mean_reversion_buy_signals(df, rocThreshold = -5):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'roc']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'roc' columns."
    
    # Create the condition for buy signals
    buy_signal_condition = (df['roc'] < rocThreshold)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buy_signal_condition, 'BUYSignal'] = 1

def remove_roc_mean_reversion_columns(df):
    df.drop(columns=['roc'], inplace=True)
    
# buyAndHolder

def create_buy_and_holder_signals(df):
    add_buy_and_holder_columns(df)
    create_buy_and_holder_buy_signals(df)
    remove_buy_and_holder_columns(df)

def add_buy_and_holder_columns(df):
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df['ema'] = ta.ema(df['Close'], length=1)
    df.dropna(inplace=True)

def create_buy_and_holder_buy_signals(df):
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date']
    assert all(col in df.columns for col in required_columns), "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date' columns."

    buy_signal_condition_ema = (df['ema'] > 0)
    df['BUYSignal'] = df['BUYSignal'] | buy_signal_condition_ema

def remove_buy_and_holder_columns(df):
    df.drop(columns=['ema'], inplace=True)

# Buy After Red Day

def create_buy_after_red_day_signals(df):
    add_buy_after_red_day_columns(df)
    create_buy_after_red_day_buy_signals(df)
    remove_buy_after_red_day_columns(df)

def add_buy_after_red_day_columns(df):
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df['prev_close'] = df['Close'].shift(1)
    df['prev_open'] = df['Open'].shift(1)
    df['ema'] = ta.ema(df['Close'], length=50)
    df.dropna(inplace=True)

def create_buy_after_red_day_buy_signals(df):
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'prev_close', 'prev_open', 'ema']
    assert all(col in df.columns for col in required_columns), "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'prev_close', 'prev_open', 'ema' columns."

    buy_signal_condition = (df['prev_close'] < df['prev_open'])

    df.loc[buy_signal_condition, 'BUYSignal'] = 1
    
def remove_buy_after_red_day_columns(df):
    df.drop(columns=['prev_close', 'prev_open', 'ema'], inplace=True)
    