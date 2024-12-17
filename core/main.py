import core.dataManipulator as dm
import strategies.strategyTester as st


if __name__ == "__main__":
    # symbols = dm.loadSymbols('SP')
    symbols = ['AMD', 'NVDA', 'CAT', 'TER', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'T', 'VZ', 'KO', 'PEP', 'JNJ', 'PG', 'UNH', 'MRK', 'PFE', 'INTC', 'CSCO', 'IBM', 'ORCL', 'QCOM', 'TXN', 'MU', 'NFLX', 'DIS', 'CMCSA', 'FOX', 'FOXA', 'DISCA', 'DISCK', 'VIAC', 'DISCB']
    # symbols = ['NVDA']

    strategy = 'buyAfterRedDay'

    st.runMasterBacktest(symbols, strategy)
