from core.plotter import plot, plot_divided
from core.utils import calculate_sharpe_ratio, calculate_optimal_portfolio, calculate_adaptive_portfolio
from pprint import pprint
import numpy as np
import pandas as pd
import json
from typing import List, Dict, Any, Optional


def log_all_results(results: List[Dict[str, Any]], strategies: Dict[str, int], find_best: bool, optimize_portfolio: bool, adaptive_portfolio: bool) -> None:
    with open('data/config.json', 'r') as file:
        config = json.load(file)

    for result in results:
        log_simple(result)

    if config['find_best'] or find_best:
        compare_results(strategies)

    if config['optimize_portfolio'] or optimize_portfolio:
        log_optimized_portfolio(results)
    elif config['adaptive_portfolio'] or adaptive_portfolio:
        log_adaptive_portfolio(results, 5, 10)
    else:
        log_aggregated_results(results)

def log(backtest_results: Dict[str, Any]) -> None:
    result_type = "W" if backtest_results['Return [%]'] > backtest_results['Buy & Hold Return [%]'] else "L"
    print(f"| {result_type} R %: {round(backtest_results['Return [%]'], 2):<7}| "
          f"B&H R %: {round(backtest_results['Buy & Hold Return [%]'], 2):<7}| "
          f"DD %: {round(backtest_results['Max. Drawdown [%]'], 2):<7}| "
          f"#T: {backtest_results['# Trades']:<4}| "
          f"In {(backtest_results['End'] - backtest_results['Start']).days} days | "
          f"Sharpe Ratio: {round(backtest_results['Sharpe Ratio'], 2):<5}| "
          f"Win Rate: {round(backtest_results['Win Rate [%]'], 2):<5} |")

def log_simple(result: Optional[Dict[str, Any]]) -> None:
    if result is None:
        return

    print(f"{result['symbol']:<5} | "
          f"Return: {round(result['return'], 2):<7}% | "
          f"Max. Drawdown: {round(-result['max_drawdown'], 2):<5}% | "
          f"Sharpe Ratio: {round(result['sharpe'], 2):<5} | "
          f"Strategy: {result['strategy']}")

def log_aggregated_results(results: List[Dict[str, Any]]) -> None:
    if not results:
        print("No results to aggregate.")
        return

    equity_curve = pd.DataFrame()
    starting_balance = 100000
    trade_count = sum(result['# trades'] for result in results)
    sharpe_sum = sum(result['sharpe'] for result in results)

    equity_curve['DrawdownPct'] = sum(result['equity_curve']['DrawdownPct'] for result in results) / len(results)
    equity_curve['Equity'] = sum(result['equity_curve']['Equity'] for result in results) / len(results)

    combined_sharpe = calculate_sharpe_ratio(equity_curve['Equity'])
    max_drawdown_index = equity_curve['DrawdownPct'].idxmax().strftime('%Y-%m-%d')

    print(f"\nFinal aggregated equity: ${round(equity_curve['Equity'].iloc[-1])}")
    print(f"Return: {round(100 * (equity_curve['Equity'].iloc[-1] - starting_balance) / starting_balance, 2)}%")
    print(f"Maximum aggregated drawdown: {round(equity_curve['DrawdownPct'].max() * 100, 2)}% at date: {max_drawdown_index}")
    print(f"Average Sharpe Ratio: {round(sharpe_sum / len(results), 2)}")
    print(f"Combined Sharpe Ratio: {round(combined_sharpe, 2)}")
    print(f"Total trades: {trade_count}")
    print(f"Average trade duration: {round(np.mean([result['avg_trade_duration'].days for result in results]), 2)} days")
    print(f"Strategy was implemented on {len(results)} symbols.")
    plot(equity_curve['Equity'])

def log_optimized_portfolio(results: List[Dict[str, Any]]) -> None:
    sharpe_threshold = 0.3
    starting_balance = 100000
    optimal_portfolio, optimal_weights, optimized_sharpe = calculate_optimal_portfolio(results, 1, sharpe_threshold)
    dfs = [result['equity_curve'] for result in results if result['sharpe'] >= sharpe_threshold]
    n_assets = len(dfs)
    equity_df_combined = sum(dfs[i]['Equity'] * optimal_weights[i] for i in range(n_assets)).dropna()
    drawdown_df_combined = sum(dfs[i]['DrawdownPct'] * optimal_weights[i] for i in range(n_assets)).dropna()
    max_drawdown_index = drawdown_df_combined.idxmax().strftime('%Y-%m-%d')

    pprint(optimal_portfolio)
    print(f"Final aggregated equity: ${round(equity_df_combined.iloc[-1])}")
    print(f"Return: {round(100 * (equity_df_combined.iloc[-1] - starting_balance) / starting_balance, 2)}%")
    print(f"Maximum aggregated drawdown: {round(drawdown_df_combined.max() * 100, 2)}% at date: {max_drawdown_index}")
    print(f"Optimized Sharpe Ratio: {round(optimized_sharpe, 2)}")
    plot(equity_df_combined)

def log_adaptive_portfolio(results: List[Dict[str, Any]], n_divisions: int = 4, strategy_limit: int = 25) -> None:
    starting_balance = 100000.0
    optimal_portfolios, sharpe_ratios = calculate_adaptive_portfolio(results, n_divisions, strategy_limit)
    division_length = len(results[0]['equity_curve']['Equity']) // n_divisions
    equity_index = results[0]['equity_curve']['Equity'].index[division_length:]
    drawdown_index = results[0]['equity_curve']['DrawdownPct'].index[division_length:]
    
    equity_df_combined = pd.Series(starting_balance, index=equity_index, dtype=float)
    drawdown_df_combined = pd.Series(0, index=drawdown_index, dtype=float)

    print(f"--------- Division 0/{n_divisions - 1} ---------")
    print("Used for optimizing.")

    for i in range(1, n_divisions):
        start_index = i * division_length
        end_index = (i + 1) * division_length
        start_index_shifted = start_index - division_length
        end_index_shifted = end_index - division_length

        previous_equity_end = equity_df_combined.iloc[start_index_shifted - 1] if start_index_shifted > 0 else starting_balance

        for symbol, data in optimal_portfolios[i - 1].items():
            current_results = [
                result for result in results
                if result['symbol'] == symbol and result['strategy'] in [df['strategy'] for df in data]
            ]

            for current_result in current_results:
                equity_curve = current_result['equity_curve']['Equity']
                drawdown_curve = current_result['equity_curve']['DrawdownPct']
                
                equity_curve_adjusted = equity_curve - equity_curve.iloc[start_index]
                drawdown_curve_adjusted = drawdown_curve - drawdown_curve.iloc[start_index]

                for strategy in data:
                    if strategy['strategy'] == current_result['strategy']:
                        equity = equity_curve_adjusted[start_index:end_index] * strategy['weight']
                        drawdown = drawdown_curve_adjusted[start_index:end_index] * strategy['weight']

                        equity_df_combined[start_index_shifted:end_index_shifted] += equity
                        drawdown_df_combined[start_index_shifted:end_index_shifted] += drawdown
                        break

        transition_value = equity_df_combined.iloc[start_index_shifted] if start_index_shifted > 0 else starting_balance
        equity_df_combined[start_index_shifted:end_index_shifted] += (previous_equity_end - transition_value)

        current_sharpe_ratio = round(calculate_sharpe_ratio(equity_df_combined[start_index_shifted:end_index_shifted]), 4)
        predicted_sharpe_ratio = round(sharpe_ratios[i - 1], 4)

        print(f"\n--------- Division {i}/{n_divisions - 1} ------------")
        print(f"Equity at start: ${round(equity_df_combined.iloc[start_index_shifted])}")
        print(f"Equity at end: ${round(equity_df_combined.iloc[end_index_shifted-1])}")
        print(f"Start date: {equity_df_combined.index[start_index_shifted].strftime('%Y-%m-%d')}")
        print(f"End date: {equity_df_combined.index[end_index_shifted-1].strftime('%Y-%m-%d')}")
        print(f"Sharpe Ratio: {current_sharpe_ratio}")
        print(f"Predicted Sharpe Ratio: {predicted_sharpe_ratio}")
        pprint(optimal_portfolios[i - 1])

    equity_df_combined = equity_df_combined.loc[equity_df_combined != starting_balance].dropna()
    adaptive_sharpe = calculate_sharpe_ratio(equity_df_combined)
    max_drawdown_index = drawdown_df_combined.idxmax().strftime('%Y-%m-%d')

    print("\n--------- Aggregated Results ---------")
    print(f"Final aggregated equity: ${round(equity_df_combined.iloc[-1])}")
    print(f"Return: {round(100 * (equity_df_combined.iloc[-1] - starting_balance) / starting_balance, 2)}%")
    print(f"Maximum aggregated drawdown: {round(drawdown_df_combined.max() * 100, 2)}% at date: {max_drawdown_index}")
    print(f"Adaptive Sharpe Ratio: {round(adaptive_sharpe, 2)}")
    plot_divided(equity_df_combined, n_divisions - 1)

def compare_results(strategies: Dict[str, int]) -> None:
    print()
    for strategy, count in strategies.items():
        print(f"Strategy {strategy} was selected {count} times.")

    most_selected_strategy = max(strategies, key=strategies.get)
    print(f"\nThe most selected strategy is {most_selected_strategy}, chosen {strategies[most_selected_strategy]} times.")
