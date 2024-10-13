import strategyTester as st
import dataManipulator as dm


if __name__ == "__main__":
    symbols = dm.loadSymbols('R2000')
    # symbols = ['AMD', 'NVDA', 'CAT']
    # symbols = ['TER']

    strategy = 'dailyRange'

    st.runMasterBacktest(symbols, strategy)
        