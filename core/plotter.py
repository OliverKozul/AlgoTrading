import matplotlib.pyplot as plt


def plot(equity):
    plt.figure(figsize=(10, 6))
    
    plt.plot(equity, label='Equity Curve', color='blue')
    
    plt.title('Trading Strategy')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_divided(equity, n_divisions):
    plt.figure(figsize=(10, 6))
    
    plt.plot(equity.index, equity, label='Equity Curve', color='blue')
    
    division_length = len(equity) // n_divisions
    for i in range(1, n_divisions):
        plt.axvline(x=equity.index[i * division_length], color='red', linestyle='--')
    
    plt.plot([equity.index[0], equity.index[-1]], [equity.iloc[0], equity.iloc[-1]], color='green', linestyle='--', label='Ideal Equity')
    
    plt.title('Trading Strategy')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.show()
    