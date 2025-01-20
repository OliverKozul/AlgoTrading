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
    
    plt.title('Trading Strategy')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.show()
    