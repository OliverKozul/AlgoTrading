import core.data_manipulator as dm
import strategies.strategy_tester as st


if __name__ == "__main__":
    # symbols = dm.load_symbols('SP')
    # symbols = ['ES=F', 'YM=F', 'NQ=F', 'RTY=F', 'ZB=F', 'GC=F', 'SI=F']
    symbols = dm.load_symbols('futures')

    strategy = 'daily_range'

    st.run_master_backtest(symbols, strategy)
