import time
import numpy as np
from scipy.optimize import minimize
from multiprocessing import Pool


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
    day_returns = equity_df.resample('D').last().dropna().pct_change()
    gmean_day_return = geometric_mean(day_returns)
    annual_trading_days = 252
    annualized_return = (1 + gmean_day_return)**annual_trading_days - 1
    annualized_return = annualized_return * 100
    annualized_volatility = np.sqrt((day_returns.var(ddof=int(bool(day_returns.shape))) + (1 + gmean_day_return)**2)**annual_trading_days - (1 + gmean_day_return)**(2*annual_trading_days)) * 100  # noqa: E501
    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility

    return sharpe_ratio

def calculate_weighted_sharpe_ratio_negative(weights, equity_dfs, risk_free_rate=0.00):
    gmean_day_return = 0.0
    day_returns = equity_dfs[0].resample('D').last().dropna().pct_change() * weights[0]
    annual_trading_days = np.nan

    for i in range(1, len(equity_dfs)):
        pct_change = equity_dfs[i].resample('D').last().dropna().pct_change()

        if pct_change.empty:
            continue
        
        day_returns += pct_change * weights[i]

    gmean_day_return = geometric_mean(day_returns)
    annual_trading_days = 252
    annualized_return = (1 + gmean_day_return)**annual_trading_days - 1
    annualized_return = annualized_return * 100
    annualized_volatility = np.sqrt((day_returns.var(ddof=int(bool(day_returns.shape))) + (1 + gmean_day_return)**2)**annual_trading_days - (1 + gmean_day_return)**(2*annual_trading_days)) * 100  # noqa: E501
    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility

    return -sharpe_ratio

def calculate_optimal_portfolio(results, sharpe_threshold=0.3):
    symbols = set()
    strategies = set()
    equity_dfs = [result['equity_curve']['Equity'] for result in results if result['sharpe'] >= sharpe_threshold]
    
    for result in results:
        symbols.add(result['symbol'])
        strategies.add(result['strategy'])

    symbols = list(symbols)
    strategies = list(strategies)
    n_assets = len(equity_dfs)

    constraints = (
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
    )
    bounds = [(0, 1) for _ in range(n_assets)]
    initial_weights = np.array([1 / n_assets] * n_assets)

    optimization_result = minimize(
        calculate_weighted_sharpe_ratio_negative,
        initial_weights,
        args=(equity_dfs,),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        tol=1e-4,
    )

    optimal_weights = optimization_result.x
    optimal_portfolio = {symbol : [] for symbol in symbols}

    for i in range(n_assets):
        if optimal_weights[i] > 0.01:
            results[i]["weight"] = round(optimal_weights[i], 4)
            optimal_portfolio[results[i]["symbol"]].append({"strategy": results[i]["strategy"], "weight": results[i]["weight"]})

    return optimal_portfolio, optimal_weights, -optimization_result.fun

def calculate_for_division(i, results, sharpe_threshold, n_divisions):
    divided_results = []
    for result in results:
        start_index = i * (len(result['equity_curve']) // n_divisions)
        end_index = (i + 1) * (len(result['equity_curve']) // n_divisions)
        divided_equity_curve = result['equity_curve'][start_index:end_index]
        divided_result = result.copy()
        divided_result['equity_curve'] = divided_equity_curve
        divided_results.append(divided_result)

    return calculate_optimal_portfolio(divided_results, sharpe_threshold)

def calculate_adaptive_portfolio(results, sharpe_threshold, n_divisions):
    all_optimal_weights = []
    optimal_portfolios = []
    sharpe_ratios = []

    with Pool() as pool:
        results = pool.starmap(calculate_for_division, [(i, results, sharpe_threshold, n_divisions) for i in range(n_divisions)])
        for optimal_portfolio, optimal_weights, sharpe_ratio in results:
            all_optimal_weights.append(optimal_weights)
            optimal_portfolios.append(optimal_portfolio)
            sharpe_ratios.append(sharpe_ratio)

    return all_optimal_weights, optimal_portfolios, sharpe_ratios
