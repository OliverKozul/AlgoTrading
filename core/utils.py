import time
import numpy as np


def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Function '{func.__name__}' took {elapsed_time:.4f} seconds to complete.")
        return result
    return wrapper

def geometric_mean(returns):
    returns = returns.fillna(0) + 1
    if np.any(returns <= 0):
        return 0
    return np.exp(np.log(returns).sum() / (len(returns) or np.nan)) - 1
    
def calculate_sharpe_ratio(equity_df, risk_free_rate=0.00):
    gmean_day_return = 0.0
    day_returns = np.array(np.nan)
    annual_trading_days = np.nan
    day_returns = equity_df['Equity'].resample('D').last().dropna().pct_change()
    gmean_day_return = geometric_mean(day_returns)
    annual_trading_days = 252
    annualized_return = (1 + gmean_day_return)**annual_trading_days - 1
    annualized_return = annualized_return * 100
    annualized_volatility = np.sqrt((day_returns.var(ddof=int(bool(day_returns.shape))) + (1 + gmean_day_return)**2)**annual_trading_days - (1 + gmean_day_return)**(2*annual_trading_days)) * 100  # noqa: E501
    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility

    return sharpe_ratio
