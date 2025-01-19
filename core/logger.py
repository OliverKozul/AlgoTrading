from core.plotter import plot
from core.utils import calculate_sharpe_ratio, calculate_optimal_portfolio
import numpy as np
import pandas as pd
from pprint import pprint


def log(backtest_results):
    if backtest_results['Return [%]'] > backtest_results['Buy & Hold Return [%]']:
        print(f"| W R %: {str(round(backtest_results['Return [%]'], 2)).ljust(7)}| "
            f"B&H R %: {str(round(backtest_results['Buy & Hold Return [%]'], 2)).ljust(7)}| "
            f"DD %: {str(round(backtest_results['Max. Drawdown [%]'], 2)).ljust(7)}| "
            f"#T: {str(backtest_results['# Trades']).ljust(4)}| "
            f"In {(backtest_results['End'] - backtest_results['Start']).days} days | "
            f"Sharpe Ratio: {str(round(backtest_results['Sharpe Ratio'], 2)).ljust(5)}| "
            f"Win Rate: {str(round(backtest_results['Win Rate [%]'], 2)).ljust(5)} |")
    else:
        print(f"| L R %: {str(round(backtest_results['Return [%]'], 2)).ljust(7)}| "
            f"B&H R %: {str(round(backtest_results['Buy & Hold Return [%]'], 2)).ljust(7)}| "
            f"DD %: {str(round(backtest_results['Max. Drawdown [%]'], 2)).ljust(7)}| "
            f"#T: {str(backtest_results['# Trades']).ljust(4)}| "
            f"In {(backtest_results['End'] - backtest_results['Start']).days} days | "
            f"Sharpe Ratio: {str(round(backtest_results['Sharpe Ratio'], 2)).ljust(5)}| "
            f"Win Rate: {str(round(backtest_results['Win Rate [%]'], 2)).ljust(5)} |")

def log_simple(result):
    if result is None:
        return
    
    print(f"{str(result['symbol']).ljust(5)} | "
            f"Return: {str(round(result['return'], 2)).ljust(7)}% | "
            f"Max. Drawdown: {str(round(-result['max_drawdown'], 2)).ljust(5)}% | "
            f"Sharpe Ratio: {str(round(result['sharpe'], 2)).ljust(5)} | "
            f"Strategy: {result['strategy']}")

def log_aggregated_results(results):
    equity_curve = pd.DataFrame()
    starting_balance = 100000
    trade_count = sum(result['# trades'] for result in results)
    sharpe_sum = sum(result['sharpe'] for result in results)

    if len(results) == 0:
        print("No results to aggregate.")
        return
    
    equity_curve['DrawdownPct'] = sum(result['equity_curve']['DrawdownPct'] for result in results) / len(results)
    equity_curve['Equity'] = sum(result['equity_curve']['Equity'] for result in results) / len(results)

    if equity_curve is None:
        print("No results to aggregate.")
        return
    
    combined_sharpe = calculate_sharpe_ratio(equity_curve['Equity'])
    
    print()
    print(f"Final aggregated equity: ${round(equity_curve['Equity'].iloc[-1])}")
    print(f"Return: {round(100 * (equity_curve['Equity'].iloc[-1] - starting_balance) / starting_balance, 2)}%")
    print(f"Maximum aggregated drawdown: {round(equity_curve['DrawdownPct'].max() * 100, 2)}%")
    print(f"Average Sharpe Ratio: {round(sharpe_sum / len(results), 2)}")
    print(f"Combined Sharpe Ratio: {round(combined_sharpe, 2)}")
    print(f"Total trades: {trade_count}")
    print(f"Average trade duration: {round(np.mean([result['avg_trade_duration'].days for result in results]), 2)} days")
    print(f"Strategy was implemented on {len(results)} symbols.")
    plot(equity_curve['Equity'])

def log_optimized_portfolio(results):
    sharpe_threshold = 0.3
    starting_balance = 100000
    optimal_portfolio, optimal_weights, optimized_sharpe = calculate_optimal_portfolio(results, sharpe_threshold)
    dfs = [result['equity_curve'] for result in results if result['sharpe'] >= sharpe_threshold]
    n_assets = len(dfs)
    equity_df_combined = sum(dfs[i]['Equity'] * optimal_weights[i] for i in range(n_assets)).dropna()
    drawdown_df_combined = sum(dfs[i]['DrawdownPct'] * optimal_weights[i] for i in range(n_assets)).dropna()

    pprint(optimal_portfolio)
    print(f"Final aggregated equity: ${round(equity_df_combined.iloc[-1])}")
    print(f"Return: {round(100 * (equity_df_combined.iloc[-1] - starting_balance) / starting_balance, 2)}%")
    print(f"Maximum aggregated drawdown: {round(drawdown_df_combined.max() * 100, 2)}%")
    print(f"Optimized Sharpe Ratio: {round(optimized_sharpe, 2)}")
    plot(equity_df_combined)

def compare_results(strategies):
    print()
    for strategy, count in strategies.items():
        print(f"Strategy {strategy} was selected {count} times.")

    most_selected_strategy = max(strategies, key=strategies.get)
    print(f"\nThe most selected strategy is {most_selected_strategy}, chosen {strategies[most_selected_strategy]} times.")
