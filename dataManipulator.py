import yfinance as yf
import pandas as pd
import pandas_ta as ta

def fetchData(symbol):
    try:
        # Attempt to download data for the given symbol
        df = yf.download(symbol, period='2y', interval='1d', progress=False)
        
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

def createSignals(df, strategy):
    if strategy == 'dailyRangeH':
        createDailyRangeSignalsH(df)

    elif strategy == 'dailyRange':
        createDailyRangeSignals(df)
    
    elif strategy == 'buyAndHold':
        return

# Daily Range Hourly

def createDailyRangeSignalsH(df):
    addDailyRangeColumnsH(df)
    createBuySignalsDailyRangeH(df)
    createSellSignalsDailyRangeH(df)
    removeDailyRangeColumnsH(df)

def addDailyRangeColumnsH(df):
    # Parameters
    EMAPeriod = 1000           # EMA Period
    MADev = 1                # MA Dev
    BBPeriod = 20            # BB period
    BBDev = 1.5              # BB Dev

    # Add columns for EMA, MA, and Bollinger Bands
    df['ma'] = ta.ema(df['Close'], length=EMAPeriod)
    df['maLower'] = df['ma'] - (df['Close'].rolling(window=EMAPeriod).std() * MADev)
    df['middleBand'] = ta.ema(df['Close'], length=BBPeriod)
    df['lowerBand'] = df['middleBand'] - (df['Close'].rolling(window=BBPeriod).std() * BBDev)
    df['width'] = (df['middleBand'] - df['Close']) / (df['middleBand'] - df['lowerBand'])
    df.dropna(inplace=True)

def createBuySignalsDailyRangeH(df, entry_hour = 7, entry_hour_final = 19, low_percentage=25, period=24):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date' columns."
    
    # Initialize the 'BUYSignal' column with default values (0)
    df['BUYSignal'] = 0
    df['currentPercent'] = 100 * (df['Close'] - df['Close'].rolling(period).min()) / (df['Close'].rolling(period).max() - df['Close'].rolling(period).min())

    buySignalCondition1 = (
        (df['currentPercent'] <= low_percentage) &  # Close price in the bottom X% of the day
        (df['Date'].dt.hour >= entry_hour) & (df['Date'].dt.hour <= entry_hour_final) & # Within entry hours
        (df['Close'] < df['middleBand']) &
        (df['Close'] > df['ma'])
    )

    buySignalCondition2 = (
        (df['currentPercent'] <= low_percentage) &  # Close price in the bottom X% of the day
        (df['Date'].dt.hour >= entry_hour) & (df['Date'].dt.hour <= entry_hour_final) & # Within entry hours
        (df['Close'] < df['maLower']) &
        (df['Close'] > df['Close'].shift(10)) &
        (df['Close'] > df['Close'].shift(5)) &
        (df['Close'] > df['Open'])
    )

    df.loc[buySignalCondition1, 'BUYSignal'] = 1
    df.loc[buySignalCondition2, 'BUYSignal'] = 2

def createSellSignalsDailyRangeH(df, highPercentage1=75, highPercentage2=35, exitHour=20, period1=36, period2=12):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date' columns."
    
    # Initialize the 'SELLSignal' column with default values (0)
    df['SELLSignal'] = 0

    # Get the maximum close price of the day
    df['currentPercent1'] = 100 * (df['Close'] - df['Close'].rolling(period1).min()) / (df['Close'].rolling(period1).max() - df['Close'].rolling(period1).min())
    df['currentPercent2'] = 100 * (df['Close'] - df['Close'].rolling(period2).min()) / (df['Close'].rolling(period2).max() - df['Close'].rolling(period2).min())

    # Create the condition for sell signals
    sellSignalCondition1 = (df['Date'].dt.hour >= exitHour) & (df['currentPercent1'] >= highPercentage1) & (df['Close'] > df['ma'])
    sellSignalCondition2 = (df['Date'].dt.hour >= exitHour) & (df['currentPercent2'] >= highPercentage2) & (df['Close'] <= df['ma'])

    # Apply the condition to the 'SELLSignal' column
    df.loc[sellSignalCondition1, 'SELLSignal'] = 1
    df.loc[sellSignalCondition2, 'SELLSignal'] = 2

def removeDailyRangeColumnsH(df):
    df.drop(columns=['currentPercent', 'currentPercent1', 'currentPercent2'], inplace=True)
    df.drop(columns=['ma', 'maLower', 'middleBand', 'lowerBand'], inplace=True)

# Daily Range

def createDailyRangeSignals(df):
    createBuySignalsDailyRange(df)

def createBuySignalsDailyRange(df, lowPercentage = 7):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date']
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date' columns."
    
    # Initialize the 'BUYSignal' column with default values (0)
    df['BUYSignal'] = 0
    df['currentPercent'] = 100 * (df['Close'] - df['Low']) / (df['High'] - df['Low'])

    buySignalCondition = (
        (df['currentPercent'] <= lowPercentage)
    )

    df.loc[buySignalCondition, 'BUYSignal'] = 1