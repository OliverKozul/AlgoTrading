import dataManipulator as dm
import strategyTester as st


if __name__ == "__main__":
    # symbols = dm.loadSymbols('SP')
    symbols = ['AMD', 'NVDA', 'CAT']
    # symbols = ['TER']

    strategy = 'soloRSI'

    st.runMasterBacktest(symbols, strategy)
