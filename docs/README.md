# Strategy Backtester with Community Strategy Creator

This project is a web-based application built with [Dash](https://dash.plotly.com/), allowing users to backtest trading strategies on S&P 500 stocks and create new trading strategies. It provides a user interface for backtesting both **official strategies** and **community strategies**, with support for persistent community strategy storage.

## Features

- **Backtesting**: Backtest multiple official and community strategies on S&P 500 companies.
- **Strategy Creator**: Create custom strategies and save them as part of the community strategy list.
- **Persistence**: Community strategies are saved in a JSON file and persist across sessions.
- **Interactive UI**: Select companies and strategies via dropdowns and view results in an interactive Plotly chart.

## Getting Started

### Prerequisites

To run this project locally, you need the following:

- Python 3.7+
- [Dash](https://dash.plotly.com/)
- Other dependencies listed in `requirements.txt`

### Installing

1. Clone this repository:

   ```bash
   git clone https://github.com/OliverKozul/AlgoTrading.git
   cd strategy-backtester
   ```
2. Install the required dependencies:

    ```bash
    pip install -r docs/requirements.txt
    ```
3. Run the app:
   ```bash
   python -m web.home
   ```

## Usage

### Backtest Strategies

1. Open the application by navigating to [http://127.0.0.1:8050/](http://127.0.0.1:8050/) in your web browser.
2. Select one or more official strategies or community strategies from the dropdowns.
3. Choose S&P 500 companies from the dropdown list.
4. Select the start and end year for the backtest.
5. Click **Run Backtest** to view the equity curve of the selected strategies.

### Create Community Strategies

1. Navigate to the **Strategy Creator** tab.
2. Define a new strategy by filling in the necessary parameters.
3. Save the strategy to add it to the community strategies list.
4. The strategy will be available in the **Community Strategies** dropdown on the **Backtest** tab.

### Official Strategies

The app supports the following official strategies:

- Buy and Hold
- Daily Range
- Solo RSI
- ROC Trend Following (Bull/Bear)
- ROC Mean Reversion

### Community Strategies

Any strategy created in the **Strategy Creator** tab is saved in `community_strategies.json` and becomes available for future sessions.

### Customization

You can customize the strategies and backtesting logic by modifying `strategy_tester.py`. For example, you can implement new strategies by adding them to the official strategy list or as community strategies.

### JSON Storage

Community strategies are saved in `community_strategies.json`. The app automatically loads this file upon startup and updates it when new strategies are added.

### Contributing

Feel free to submit issues or pull requests if you want to contribute to the project.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

