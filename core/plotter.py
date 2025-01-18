import matplotlib.pyplot as plt


def plot(equity):
    """
    Plots the equity curve and drawdown curve of a trading strategy.

    Parameters:
    equity (list or array-like): The equity values over time.

    Returns:
    None
    """
    plt.figure(figsize=(10, 6))
    
    # Plot equity curve
    plt.plot(equity, label='Equity Curve', color='blue')
    
    plt.title('Trading Strategy')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.show()
    