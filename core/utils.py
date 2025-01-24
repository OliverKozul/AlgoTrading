import time
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from multiprocessing import Pool
from typing import Callable, List, Dict, Tuple, Any


def timeit(func: Callable) -> Callable:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Function '{func.__name__}' took {elapsed_time:.4f} seconds to complete.")
        return result
    return wrapper

def geometric_mean(returns: pd.Series) -> float:
    returns = returns.fillna(0) + 1
    if np.any(returns <= 0):
        return 0
    return np.exp(np.log(returns).sum() / (len(returns) or np.nan)) - 1

def calculate_sharpe_ratio(equity_df: pd.DataFrame, risk_free_rate: float = 0.03) -> float:
    gmean_day_return = 0.0
    day_returns = np.array(np.nan)
    annual_trading_days = np.nan
    day_returns = equity_df.resample('D').last().dropna().pct_change()
    gmean_day_return = geometric_mean(day_returns)
    annual_trading_days = 252
    annualized_return = (1 + gmean_day_return)**annual_trading_days - 1
    annualized_return = annualized_return * 100
    annualized_volatility = np.sqrt((day_returns.var(ddof=int(bool(day_returns.shape))) + (1 + gmean_day_return)**2)**annual_trading_days - (1 + gmean_day_return)**(2*annual_trading_days)) * 100  # noqa: E501
    
    if annualized_volatility == 0:
        return -1
    
    sharpe_ratio = (annualized_return - risk_free_rate * 100) / annualized_volatility

    return sharpe_ratio

def calculate_weighted_sharpe_ratio_negative(weights: np.ndarray, equity_dfs_pct_change: List[pd.Series], risk_free_rate: float = 0.03) -> float:
    gmean_day_return = 0.0
    day_returns = equity_dfs_pct_change[0] * weights[0]
    annual_trading_days = np.nan

    for i in range(1, len(equity_dfs_pct_change)):
        if equity_dfs_pct_change[i].empty:
            continue
        
        day_returns += equity_dfs_pct_change[i] * weights[i]

    gmean_day_return = geometric_mean(day_returns)
    annual_trading_days = 252
    annualized_return = (1 + gmean_day_return)**annual_trading_days - 1
    annualized_return = annualized_return * 100
    annualized_volatility = np.sqrt((day_returns.var(ddof=int(bool(day_returns.shape))) + (1 + gmean_day_return)**2)**annual_trading_days - (1 + gmean_day_return)**(2*annual_trading_days)) * 100  # noqa: E501
    
    if annualized_volatility == 0:
        return 1
    
    sharpe_ratio = (annualized_return - risk_free_rate * 100) / annualized_volatility

    return -sharpe_ratio

def calculate_optimal_portfolio(results: List[Dict[str, Any]], strategy_limit: int) -> Tuple[Dict[str, List[Dict[str, Any]]], float]:
    symbols = set()
    strategies = set()
    sharpe_threshold = -1.0
    count = sum(result['sharpe'] >= sharpe_threshold for result in results)

    while count > strategy_limit:
        sharpe_threshold += 0.025
        count = sum(result['sharpe'] >= sharpe_threshold for result in results)

    results = [result for result in results if result['sharpe'] >= sharpe_threshold]
    equity_dfs_pct_change = [result['equity_curve']['Equity'].resample('D').last().dropna().pct_change() for result in results]
    
    for result in results:
        symbols.add(result['symbol'])
        strategies.add(result['strategy'])

    symbols = list(symbols)
    strategies = list(strategies)
    n_assets = len(equity_dfs_pct_change)

    if n_assets == 0:
        return {}, 0

    constraints = (
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "ineq", "fun": lambda w: w - 1 / (n_assets * 2)},
    )
    bounds = [(0, 1) for _ in range(n_assets)]
    initial_weights = np.array([1 / n_assets] * n_assets)

    optimization_result = minimize(
        calculate_weighted_sharpe_ratio_negative,
        initial_weights,
        args=(equity_dfs_pct_change,),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )

    optimal_weights = optimization_result.x
    optimal_portfolio = {symbol : [] for symbol in symbols}

    for i in range(n_assets):
        if optimal_weights[i] > 0.01:
            results[i]["weight"] = round(optimal_weights[i], 4)
            optimal_portfolio[results[i]["symbol"]].append({"strategy": results[i]["strategy"], "weight": results[i]["weight"], "sharpe": results[i]["sharpe"]})

    for symbol in symbols:
        if not optimal_portfolio[symbol]:
            optimal_portfolio.pop(symbol)
            
    return optimal_portfolio, -optimization_result.fun

def calculate_for_division(i: int, results: List[Dict[str, Any]], strategy_limit: int, n_divisions: int) -> Tuple[Dict[str, List[Dict[str, Any]]], float]:
    divided_results = []

    for result in results:
        start_index = i * (len(result['equity_curve']) // n_divisions)
        end_index = (i + 1) * (len(result['equity_curve']) // n_divisions)
        divided_equity_curve = result['equity_curve'][start_index:end_index]
        divided_result = result.copy()
        divided_result['equity_curve'] = divided_equity_curve
        divided_result['sharpe'] = round(calculate_sharpe_ratio(divided_result['equity_curve']['Equity']), 4)
        divided_results.append(divided_result)

    return calculate_optimal_portfolio(divided_results, strategy_limit)

def calculate_adaptive_portfolio(results: List[Dict[str, Any]], n_divisions: int, strategy_limit: int = 25) -> Tuple[List[Dict[str, List[Dict[str, Any]]]], List[float]]:
    optimal_portfolios = []
    sharpe_ratios = []

    with Pool() as pool:
        results = pool.starmap(calculate_for_division, [(i, results, strategy_limit, n_divisions) for i in range(n_divisions)])
        for optimal_portfolio, sharpe_ratio in results:
            optimal_portfolios.append(optimal_portfolio)
            sharpe_ratios.append(sharpe_ratio)

    return optimal_portfolios, sharpe_ratios
