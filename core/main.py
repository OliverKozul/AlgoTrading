import core.dataManipulator as dm
import strategies.strategyTester as st


if __name__ == "__main__":
    # symbols = dm.loadSymbols('SP')
    # symbols = ['ES=F', 'YM=F', 'NQ=F', 'RTY=F', 'ZB=F', 'GC=F', 'SI=F']
    symbols = dm.loadSymbols('futures')

    strategy = 'dailyRange'

    st.runMasterBacktest(symbols, strategy)
