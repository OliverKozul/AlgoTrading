import yfinance as yf
import pandas as pd
import pandas_ta as ta
import re
import json
import pickle
import os
from multiprocessing import Pool
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable, Any
from strategies.strategy_tester import load_strategies_from_json


def fetch_data(symbol: str, startDate: Optional[str] = None, endDate: Optional[str] = None) -> Optional[pd.DataFrame]:
    try:
        df = yf.download(symbol, start=startDate, end=endDate, period='5y', interval='1d', progress=False, multi_level_index=False, auto_adjust=True)
        
        if df.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        
        df = df.reset_index()
        df.dropna(inplace=True)
        
        return df

    except Exception as e:
        print(f"Error fetching data for symbol {symbol}: {e}")
        return None

def fetch_data_multiple(symbols: List[str], startDate: Optional[str] = None, endDate: Optional[str] = None) -> Optional[pd.DataFrame]:
    try:
        dfs = yf.download(symbols, start=startDate, end=endDate, period='5y', interval='1d', progress=False, multi_level_index=False, auto_adjust=True)

        if dfs.empty:
            raise ValueError("No data found for given symbols")

        dfs.drop(columns=['Adj Close', 'Volume'], inplace=True)

        return dfs

    except Exception as e:
        print(f"Error fetching data for symbols: {e}")
        return None
    
def fetch_data_or_load_cached(symbols: List[str]) -> Dict[str, pd.DataFrame]:
    with open('data/index_info.json', 'r') as file:
        stock_data_info = json.load(file)

    def should_download(category: str) -> bool:
        last_download = stock_data_info[category]['last_download_date']

        if last_download is None:
            return True
        
        last_download_date = datetime.strptime(last_download, '%Y-%m-%d')
        print(f"Last download date for requested stock data: {last_download_date}")

        return datetime.now() - last_download_date >= timedelta(days=7) or not os.path.exists(f'data/{category.lower()}.pkl')

    def save_data(category: str, stock_data: Dict[str, pd.DataFrame]) -> None:
        stock_data_info[category]['last_download_date'] = datetime.now().strftime('%Y-%m-%d')
        
        with open('data/index_info.json', 'w') as file:
            json.dump(stock_data_info, file, indent=4)

        with open(f'data/{category}.pkl', 'wb') as file:
            pickle.dump(stock_data, file)

    def load_data(category: str):
        with open(f'data/{category}.pkl', 'rb') as file:
            return pickle.load(file)

    category = None

    if symbols == load_symbols('SP'):
        category = 'sp'
    elif symbols == load_symbols('NQ'):
        category = 'nq'
    elif symbols == load_symbols('R2000'):
        category = 'r2000'

    if category:
        if should_download(category):
            print("Downloading new stock data.")
            
            with Pool() as pool:
                stock_data = dict(zip(symbols, pool.map(fetch_data, symbols)))

            stock_data = clean_stock_data(stock_data, symbols)
            save_data(category, stock_data)
        else:
            print("Loading cached stock data.")
            stock_data = load_data(category)
    else:
        print("No category found for requested symbols. Downloading new stock data.")

        with Pool() as pool:
            stock_data = dict(zip(symbols, pool.map(fetch_data, symbols)))

        stock_data = clean_stock_data(stock_data, symbols)

    return stock_data

def load_cached_results(symbols: List[str], strategies: List[str]) -> Optional[List[Dict[str, Any]]]:
    with open('data/index_info.json', 'r') as file:
        stock_data_info = json.load(file)
    
    results = None
    category = None

    if symbols == load_symbols('SP'):
        category = 'sp'
    elif symbols == load_symbols('NQ'):
        category = 'nq'
    elif symbols == load_symbols('R2000'):
        category = 'r2000'

    if category is None:
        return None
    
    if stock_data_info[category]['strategies'] != strategies or datetime.now() - datetime.strptime(stock_data_info[category]['last_backtest_date'], '%Y-%m-%d') >= timedelta(days=7):
        return None

    if os.path.exists(f'data/{category}_results.pkl'):
        print("Cached results found. Loading cached results.")
        with open(f'data/{category}_results.pkl', 'rb') as file:
            results = pickle.load(file)

    return results

def save_results(results: List[Dict[str, Any]], strategies: List[str], symbols: List[str]) -> None:
    with open('data/index_info.json', 'r') as file:
        stock_data_info = json.load(file)

    print("Saving results.")

    category = None

    if symbols == load_symbols('SP'):
        category = 'sp'
    elif symbols == load_symbols('NQ'):
        category = 'nq'
    elif symbols == load_symbols('R2000'):
        category = 'r2000'

    if category is None:
        return

    stock_data_info[category]['last_backtest_date'] = datetime.now().strftime('%Y-%m-%d')
    stock_data_info[category]['strategies'] = strategies

    with open('data/index_info.json', 'w') as file:
        json.dump(stock_data_info, file, indent=4)

    with open(f'data/{category}_results.pkl', 'wb') as file:
        pickle.dump(results, file)

def load_symbols(category: str) -> Optional[List[str]]:
    if category == 'SP':
        return pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist() + ['SPY']
    elif category == 'NQ':
        return pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')[4]['Ticker'].tolist()
    elif category == 'R2000':
        return pd.read_csv('data/R2000.csv').iloc[:, 0].tolist()
    elif category == 'futures':
        return ['ES=F', 'YM=F', 'NQ=F', 'RTY=F', 'CL=F', 'GC=F', 'SI=F', 'HG=F', 'PL=F', 'PA=F', 'NG=F', 'ZB=F', 'ZT=F', 'ZN=F', 'ZS=F', 'ZW=F', 'ZC=F', 'ZL=F', 'ZM=F']
    else:
        print("Invalid index specified.")
        return None

def camel_case_to_name(camel_case_str: str) -> str:
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', camel_case_str).title()

def snake_case_to_name(snake_case_str: str) -> str:
    return snake_case_str.replace('_', ' ')

def clean_stock_data(stock_data: Dict[str, pd.DataFrame], symbols: List[str]) -> Dict[str, pd.DataFrame]:
    symbols_to_remove = [symbol for symbol, data in stock_data.items() if data is None]

    for symbol in symbols_to_remove:
        stock_data.pop(symbol)
        symbols.remove(symbol)

    max_length = max(len(data) for data in stock_data.values())

    if any(len(data) != max_length for data in stock_data.values()):
        print(f"Data length mismatch. Removing all stocks that are not of length: {max_length}.")
    else:
        print(f"All data lengths are equal length: {max_length}.")

    symbols_to_remove = [symbol for symbol, data in stock_data.items() if len(data) != max_length]

    for symbol in symbols_to_remove:
        stock_data.pop(symbol)
        symbols.remove(symbol)

    print(f"Remaining symbol count after cleaning: {len(symbols)}")

    return stock_data

def generate_simple_result(symbol: str, strategy: str, result: Dict[str, Any]) -> Dict[str, Any]:
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

def calculate_n_day_returns(df: pd.DataFrame, n: int) -> float:
    df.loc[df['BUYSignal'] == 1, f'{n}_day_return'] = df['Close'].shift(-n-1).pct_change(fill_method=None) * 100
    average_return = df.loc[df['BUYSignal'] == 1, f'{n}_day_return'].mean()
    df.drop(columns=[f'{n}_day_return'], inplace=True)

    return average_return

def create_signals(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    df['BUYSignal'] = 0

    signal_functions = load_strategies_from_json('strategies\strategies.json')
    signal_functions.update(load_strategies_from_json('strategies\community_strategies.json'))

    for key in signal_functions:
        strategy_name_words = key.split('_')
        strategy_name = ''.join([word.lower() + "_" for word in strategy_name_words])
        function_name = f"create_{strategy_name}signals"
        signal_functions[key] = globals().get(function_name)

    signal_functions.get(strategy, lambda df: None)(df)
    df = df[int(-0.9 * len(df)):].copy()

    if 'Date' in df.columns:
        df.set_index('Date', inplace=True)
    elif 'Datetime' in df.columns:
        df.set_index('Datetime', inplace=True)
        
    df.dropna(inplace=True)

    return df

def add_columns(columns: Dict[str, Callable[[pd.DataFrame], Any]]) -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(df: pd.DataFrame, *args: Any, **kwargs: Any) -> Any:
            for col, calc in columns.items():
                df[col] = calc(df)
            result = func(df, *args, **kwargs)
            columns_to_drop = [col for col in columns.keys() if col != 'atr']
            df.drop(columns=columns_to_drop, inplace=True)
            return result
        return wrapper
    return decorator

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14)})
def create_buy_and_hold_signals(df: pd.DataFrame) -> None:
    df['BUYSignal'] = 1

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14), 'current_percent': lambda df: 100 * (df['Close'] - df['Low']) / (df['High'] - df['Low'])})
def create_daily_range_signals(df: pd.DataFrame, low_percentage: int = 10) -> None:
    df.loc[df['current_percent'] <= low_percentage, 'BUYSignal'] = 1

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14), 'rsi': lambda df: ta.rsi(df['Close'], length=2)})
def create_solo_rsi_signals(df: pd.DataFrame, rsi_threshold: int = 10) -> None:
    df.loc[df['rsi'] < rsi_threshold, 'BUYSignal'] = 1

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14), 'roc': lambda df: ta.roc(df['Close'], length=60)})
def create_roc_trend_following_bull_signals(df: pd.DataFrame, rocThreshold: int = 30) -> None:
    df.loc[df['roc'] > rocThreshold, 'BUYSignal'] = 1

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14), 'roc': lambda df: ta.roc(df['Close'], length=60)})
def create_roc_trend_following_bear_signals(df: pd.DataFrame, rocThreshold: int = -30) -> None:
    df.loc[df['roc'] < rocThreshold, 'BUYSignal'] = 2

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14), 'roc': lambda df: ta.roc(df['Close'], length=10), 'prev_roc': lambda df: ta.roc(df['Close'], length=14).shift(1)})
def create_roc_mean_reversion_signals(df: pd.DataFrame, rocThreshold: int = -3) -> None:
    df.loc[(df['roc'] < rocThreshold) & (df['roc'] > df['prev_roc']), 'BUYSignal'] = 1

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14), 'ema': lambda df: ta.ema(df['Close'], length=1)})
def create_buy_and_holder_signals(df: pd.DataFrame) -> None:
    df.loc[df['ema'] > 0, 'BUYSignal'] = 1

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14), 'prev_close': lambda df: df['Close'].shift(1), 'prev_open': lambda df: df['Open'].shift(1)})
def create_buy_after_red_day_signals(df: pd.DataFrame) -> None:
    df.loc[df['prev_close'] < df['prev_open'], 'BUYSignal'] = 1

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14), 'prev_close': lambda df: df['Close'].shift(1), 'prev_open': lambda df: df['Open'].shift(1)})
def create_buy_after_green_day_signals(df: pd.DataFrame) -> None:
    df.loc[df['prev_close'] > df['prev_open'], 'BUYSignal'] = 1

@add_columns({'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14), 'rsi': lambda df: ta.rsi(df['Close'], length=14)})
def create_shorting_rsi_signals(df: pd.DataFrame) -> None:
    df.loc[df['rsi'] < 85, 'BUYSignal'] = 2

@add_columns({
    'atr': lambda df: ta.atr(df['High'], df['Low'], df['Close'], length=14),
    'macd': lambda df: ta.macd(df['Close'], fast=12, slow=26, signal=9)['MACD_12_26_9'],
    'macd_signal': lambda df: ta.macd(df['Close'], fast=12, slow=26, signal=9)['MACDs_12_26_9'],
    'stoch_k': lambda df: ta.stoch(df['High'], df['Low'], df['Close'])['STOCHk_14_3_3'],
    'stoch_d': lambda df: ta.stoch(df['High'], df['Low'], df['Close'])['STOCHd_14_3_3'],
    'rsi': lambda df: ta.rsi(df['Close'], length=14),
    'rsi_sma': lambda df: ta.rsi(df['Close'], length=14).rolling(window=14).mean()
})
def create_macd_stoch_rsi_signals(df: pd.DataFrame) -> None:
    df['macd_crossover'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
    df['stoch_in_range'] = (df['stoch_k'] > 20) & (df['stoch_k'] < 80)
    df['stoch_recently_below_20'] = df['stoch_k'].rolling(window=10).min().shift(1) < 20
    df['rsi_above_sma'] = df['rsi'] > df['rsi_sma']

    df.loc[
        df['macd_crossover'] & df['stoch_in_range'] & df['stoch_recently_below_20'] & df['rsi_above_sma'],
        'BUYSignal'
    ] = 1
