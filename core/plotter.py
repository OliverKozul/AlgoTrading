import pandas as pd
import matplotlib.pyplot as plt


def setup_plot(title: str, xlabel: str, ylabel: str):
    plt.figure(figsize=(10, 6))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)

def show_plot():
    plt.legend()
    plt.show()

def plot(equity: pd.Series):
    setup_plot('Trading Strategy', 'Time', 'Value')
    plt.plot(equity, label='Equity Curve', color='blue')
    show_plot()

def plot_divided(equity: pd.Series, n_divisions: int):
    setup_plot('Trading Strategy', 'Time', 'Value')
    plt.plot(equity.index, equity, label='Equity Curve', color='blue')
    
    for i in range(1, n_divisions):
        plt.axvline(x=equity.index[(i * len(equity)) // n_divisions], color='red', linestyle='--')
    
    plt.plot([equity.index[0], equity.index[-1]], [equity.iloc[0], equity.iloc[-1]], color='green', linestyle='--', label='Ideal Equity')
    show_plot()
