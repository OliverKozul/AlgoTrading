import strategyTester as st
import dataManipulator as dm


if __name__ == "__main__":
    symbols = dm.loadSymbols('SP')
    # symbols = ['AMD', 'NVDA', 'CAT']
    # symbols = ['TER']

    strategy = 'rocTrendFollowingBull'

    st.runMasterBacktest(symbols, strategy)
        