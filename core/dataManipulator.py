import yfinance as yf
import pandas as pd
import pandas_ta as ta
import re
import strategies.strategyTester as st


def fetchData(symbol, start = None, end = None):
    try:
        # Attempt to download data for the given symbol
        df = yf.download(symbol, start=start, end=end, period='2y', interval='1d', progress=False)
        
        # Check if the dataframe is empty (if data could not be fetched)
        if df.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        
        df = df.reset_index()
        df.drop(columns=['Adj Close', 'Volume'], inplace=True)
        df.dropna(inplace=True)
        
        return df

    except Exception as e:
        # Log the error and return None to signify the failure
        print(f"Error fetching data for symbol {symbol}: {e}")
        return None

def loadSymbols(index):
    if index == 'SP':
        return pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
    
    elif index == 'R2000':
        return pd.read_csv('R2000.csv').iloc[:, 0].tolist()
    
    else:
        print("Invalid index specified.")
        return None

def camelCaseToName(camelCaseStr):
    # Add a space before each capital letter and capitalize the first letter of the string
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', camelCaseStr).title()

def generateSimpleResult(symbol, strategy, result):
    simplifiedResult = {
        'symbol': symbol,
        'maxDrawdown': result['Max. Drawdown [%]'],
        'return': result['Return [%]'],
        'sharpe': result['Sharpe Ratio'],
        '# trades': result['# Trades'],
        'avgTradeDuration': result['Avg. Trade Duration'],
        'equity_curve': result['_equity_curve'],
        'strategy': strategy
    }

    return simplifiedResult

def createSignals(df, strategy):
    # signal_functions = {
    #     'buyAndHold': createBuyAndHoldSignals,
    #     'dailyRange': createDailyRangeSignals,
    #     'soloRSI': createSoloRSISignals,
    #     'rocTrendFollowingBull': createROCTrendFollowingBullSignals,
    #     'rocTrendFollowingBear': createROCTrendFollowingBearSignals,
    #     'rocMeanReversion': createROCMeanReversionSignals
    # }

    df['BUYSignal'] = 0

    signal_functions = st.loadStrategiesFromJson('strategies\strategies.json')
    signal_functions.update(st.loadStrategiesFromJson('strategies\communityStrategies.json'))

    for key in signal_functions:
        function_name = f"create{key[0].upper()}{key[1:]}Signals"
        signal_functions[key] = globals().get(function_name)

    signal_functions.get(strategy, lambda x: None)(df)
    df.set_index('Date', inplace=True)


def createBuyAndHoldSignals(df):
    df['BUYSignal'] = 1
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

# Daily Range

def createDailyRangeSignals(df):
    addDailyRangeColumns(df)
    createDailyRangeBuySignals(df)
    removeDailyRangeColumns(df)

def addDailyRangeColumns(df):
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df['currentPercent'] = 100 * (df['Close'] - df['Low']) / (df['High'] - df['Low'])
    df.dropna(inplace=True)

def createDailyRangeBuySignals(df, lowPercentage = 10):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'currentPercent']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'currentPercent' columns."
    
    # Create the condition for buy signals
    buySignalCondition = (df['currentPercent'] <= lowPercentage)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buySignalCondition, 'BUYSignal'] = 1

def removeDailyRangeColumns(df):
    df.drop(columns=['currentPercent'], inplace=True)

# Solo RSI

def createSoloRSISignals(df):
    addSoloRSIColumns(df)
    createSoloRSIBuySignals(df)
    removeSoloRSIColumns(df)

def addSoloRSIColumns(df, rsiPeriod = 2):
    df['rsi'] = ta.rsi(df['Close'], length=rsiPeriod)
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

def createSoloRSIBuySignals(df, rsiThreshold = 10):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'rsi']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'rsi' columns."

    # Create the condition for buy signals
    buySignalCondition = (df['rsi'] < rsiThreshold)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buySignalCondition, 'BUYSignal'] = 1

def removeSoloRSIColumns(df):
    df.drop(columns=['rsi'], inplace=True)

# ROC Trendfollowing Bull

def createRocTrendFollowingBullSignals(df):
    addROCTrendFollowingBullColumns(df)
    createROCTrendFollowingBullBuySignals(df)
    removeROCTrendFollowingBullColumns(df)

def addROCTrendFollowingBullColumns(df, rocPeriod = 60):
    df['roc'] = ta.roc(df['Close'], length=rocPeriod)
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

def createROCTrendFollowingBullBuySignals(df, rocThreshold = 30):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'roc']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'roc' columns."
    
    # Create the condition for buy signals
    buySignalCondition = (df['roc'] > rocThreshold)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buySignalCondition, 'BUYSignal'] = 1

def removeROCTrendFollowingBullColumns(df):
    df.drop(columns=['roc'], inplace=True)

# ROC Trendfollowing Bear

def createRocTrendFollowingBearSignals(df):
    addROCTrendFollowingBearColumns(df)
    createROCTrendFollowingBearBuySignals(df)
    removeROCTrendFollowingBearColumns(df)

def addROCTrendFollowingBearColumns(df, rocPeriod = 60):
    df['roc'] = ta.roc(df['Close'], length=rocPeriod)
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

def createROCTrendFollowingBearBuySignals(df, rocThreshold = -30):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'roc']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'roc' columns."
    
    # Create the condition for buy signals
    buySignalCondition = (df['roc'] < rocThreshold)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buySignalCondition, 'BUYSignal'] = 1

def removeROCTrendFollowingBearColumns(df):
    df.drop(columns=['roc'], inplace=True)

# ROC Mean Reversion

def createRocMeanReversionSignals(df):
    addROCMeanReversionColumns(df)
    createROCMeanReversionBuySignals(df)
    removeROCMeanReversionColumns(df)

def addROCMeanReversionColumns(df, rocPeriod = 14):
    df['roc'] = ta.roc(df['Close'], length=rocPeriod)
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df.dropna(inplace=True)

def createROCMeanReversionBuySignals(df, rocThreshold = -5):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date', 'roc']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date', 'roc' columns."
    
    # Create the condition for buy signals
    buySignalCondition = (df['roc'] < rocThreshold)

    # Apply the condition to the 'BUYSignal' column
    df.loc[buySignalCondition, 'BUYSignal'] = 1

def removeROCMeanReversionColumns(df):
    df.drop(columns=['roc'], inplace=True)

    
# buyAndHolder

def createBuyAndHolderSignals(df):
    addbuyAndHolderColumns(df)
    createbuyAndHolderBuySignals(df)
    removebuyAndHolderColumns(df)

def addbuyAndHolderColumns(df):
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df['ema'] = ta.ema(df['Close'], length=1)
    df.dropna(inplace=True)

def createbuyAndHolderBuySignals(df):
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date']
    assert all(col in df.columns for col in required_columns), "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date' columns."

    buySignalCondition_ema = (df['ema'] > 0)
    df['BUYSignal'] = df['BUYSignal'] | buySignalCondition_ema

def removebuyAndHolderColumns(df):
    df.drop(columns=['ema'], inplace=True)