import core.plotter as plotter
import numpy as np
import pandas as pd

def log(results):
    backtestResults = results

    if backtestResults['Return [%]'] > backtestResults['Buy & Hold Return [%]']:
        print(f"| W R %: {str(round(backtestResults['Return [%]'], 2)).ljust(7)}| "
            f"B&H R %: {str(round(backtestResults['Buy & Hold Return [%]'], 2)).ljust(7)}| "
            f"DD %: {str(round(backtestResults['Max. Drawdown [%]'], 2)).ljust(7)}| "
            f"#T: {str(backtestResults['# Trades']).ljust(4)}| "
            f"In {(backtestResults['End'] - backtestResults['Start']).days} days | "
            f"Sharpe Ratio: {str(round(backtestResults['Sharpe Ratio'], 2)).ljust(5)}| "
            f"Win Rate: {str(round(backtestResults['Win Rate [%]'], 2)).ljust(5)} |")
    else:
        print(f"| L R %: {str(round(backtestResults['Return [%]'], 2)).ljust(7)}| "
            f"B&H R %: {str(round(backtestResults['Buy & Hold Return [%]'], 2)).ljust(7)}| "
            f"DD %: {str(round(backtestResults['Max. Drawdown [%]'], 2)).ljust(7)}| "
            f"#T: {str(backtestResults['# Trades']).ljust(4)}| "
            f"In {(backtestResults['End'] - backtestResults['Start']).days} days | "
            f"Sharpe Ratio: {str(round(backtestResults['Sharpe Ratio'], 2)).ljust(5)}| "
            f"Win Rate: {str(round(backtestResults['Win Rate [%]'], 2)).ljust(5)} |")

def logSimple(result):
    if result is None:
        return
    
    print(f"{str(result['symbol']).ljust(5)} | "
            f"Return: {str(round(result['return'], 2)).ljust(7)}% | "
            f"Max. Drawdown: {str(round(-result['maxDrawdown'], 2)).ljust(5)}% | "
            f"Sharpe: {str(round(result['sharpe'], 2)).ljust(5)} | "
            f"Strategy: {result['strategy']}")

def logAggregatedResults(results):
    equityCurve = pd.DataFrame()
    startingBalance = 100000
    tradeCount = sum(result['# trades'] for result in results)
    sharpeSum = sum(result['sharpe'] for result in results)

    if len(results) == 0:
        print("No results to aggregate.")
        return
    
    equityCurve['DrawdownPct'] = sum(result['equity_curve']['DrawdownPct'] for result in results) / len(results)
    equityCurve['Equity'] = sum(result['equity_curve']['Equity'] for result in results) / len(results)

    # Kinda sus
    if equityCurve is None:
        print("No results to aggregate.")
        return
    
    equityCurve.dropna(inplace=True)
    
    print()
    print(f"Final aggregated equity: ${round(equityCurve['Equity'].iloc[-1])}")
    print(f"Return: {round(100 * (equityCurve['Equity'].iloc[-1] - startingBalance) / startingBalance, 2)}%")
    print(f"Maximum aggregated drawdown: {round(equityCurve['DrawdownPct'].max() * 100, 2)}%")
    print(f"Average Sharpe Ratio: {round(sharpeSum / len(results), 2)}")
    print(f"Total trades: {tradeCount}")
    print(f"Average trade duration: {round(np.mean([result['avgTradeDuration'].days for result in results]), 2)} days")
    print(f"Strategy was implemented on {len(results)} symbols.")
    plotter.plot(equityCurve['Equity'])

def compareResults(strategies):
    print()
    for strategy, count in strategies.items():
                print(f"Strategy {strategy} was selected {count} times.")

    mostSelectedStrategy = max(strategies, key=strategies.get)
    print(f"\nThe most selected strategy is {mostSelectedStrategy}, chosen {strategies[mostSelectedStrategy]} times.")