from dash import dcc, html, Input, Output, State
from dash import dash_table
from strategies.strategy_tester import run_master_backtest, run_backtest_process, find_best_backtest, run_adaptive_backtest, load_strategies_from_json
from core.data_manipulator import load_symbols, snake_case_to_name
import pandas as pd


symbols = load_symbols('SP')
symbols.insert(0, "ALL")
strategies_dict = load_strategies_from_json('strategies\strategies.json')
community_strategies_dict = load_strategies_from_json('strategies\community_strategies.json')


def create_backtesting_tab_layout():
    return html.Div([
        html.H3("Run Backtesting", style={"textAlign": "center", "marginBottom": "20px", "color": "#FFFFFF"}),

        html.Div([
            html.Label("Select Instruments:", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id="backtest-instruments-dropdown",
                options=[{'label': symbol, 'value': symbol} for symbol in symbols],
                multi=True,
                placeholder="Choose instruments...",
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        html.Div([
            html.Label("Select Backtesting Type:", style={"color": "#FFFFFF"}),
            dcc.RadioItems(
                id="backtest-type-radio",
                options=[
                    {"label": "Compare Strategies", "value": "compare_strategies"},
                    {"label": "Find Best Strategy", "value": "find_best"},
                    {"label": "Adaptive Strategy", "value": "adaptive_strategy"},
                    {"label": "Single Strategy", "value": "single_strategy"}
                ],
                value="compare_strategies",
                style={"color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        html.Div([
            html.Label("Select Strategy:", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id="backtest-strategy-dropdown",
                options=[{'label': snake_case_to_name(key), 'value': key}for key in strategies_dict.keys()],
                placeholder="Choose a strategy...",
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        html.Button("Run Backtests", id="run-backtest-button", style={"backgroundColor": "#1E90FF", "color": "#FFFFFF", "marginTop": "10px", "fontSize": "16px", "padding": "10px 20px"}),

        html.Div(id="backtest-results", style={"marginTop": "20px", "color": "#FFFFFF"})
    ], style={"backgroundColor": "#121212", "padding": "20px"})


def register_callbacks(app):
    @app.callback(
        Output("backtest-results", "children"),
        Input("run-backtest-button", "n_clicks"),
        State("backtest-instruments-dropdown", "value"),
        State("backtest-type-radio", "value"),
        State("backtest-strategy-dropdown", "value")
    )
    def run_backtest_callback(n_clicks, instruments, backtest_type, selected_strategy):
        if not n_clicks:
            return None

        if not instruments:
            return "Please select at least one instrument."

        if "ALL" in instruments:
            instruments = symbols[1:]

        if backtest_type == "single_strategy" and not selected_strategy:
            return "Please select a strategy for this backtesting type."

        # Run the appropriate backtest based on the selected type
        if backtest_type == "compare_strategies":
            results = run_master_backtest(instruments, selected_strategy, compare_strategies=True, plot_results=False)
        elif backtest_type == "find_best":
            results = run_master_backtest(instruments, selected_strategy, find_best=True, plot_results=False)
        elif backtest_type == "adaptive_strategy":
            results = run_master_backtest(instruments, selected_strategy, adaptive_strategy=True, plot_results=False)
        elif backtest_type == "single_strategy":
            results = run_master_backtest(instruments, selected_strategy, plot_results=False)

        if not results:
            return "No results generated. Please check your selections."

        # Process the results to structure the data for display
        # table_data = []
        # for result in results:
        #     table_data.append({
        #         "Instrument": result['symbol'],
        #         "Return": f"{result['return']:.2f} %",
        #         "Max. Drawdown": f"{result['maxDrawdown']:.2f} %",
        #         "Sharpe": f"{result['sharpe']:.2f}",
        #         "# Trades": result['# trades'],
        #         "Avg Trade Duration": str(result['avgTradeDuration']),
        #         "Strategy": snake_case_to_name(result['strategy'])
        #     })
        
        table_data = process_results_to_table(results)

        # Create the Dash DataTable
        return dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Instrument", "id": "Instrument"},
                {"name": "Return", "id": "Return"},
                {"name": "Max. Drawdown", "id": "Max. Drawdown"},
                {"name": "Sharpe", "id": "Sharpe"},
                {"name": "# Trades", "id": "# Trades"},
                {"name": "Avg Trade Duration", "id": "Avg Trade Duration"},
                {"name": "Strategy", "id": "Strategy"}
            ],
            style_table={'overflowX': 'auto', 'backgroundColor': '#333333', 'color': '#FFFFFF'},
            style_header={"backgroundColor": "#444444", "color": "#FFFFFF", "fontWeight": "bold"},
            style_cell={
                "textAlign": "center", 
                "backgroundColor": "#222222", 
                "color": "#FFFFFF", 
                "padding": "5px"
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#2A2A2A"},
            ],
            sort_action="native",
            page_size=25
        )

def process_results_to_table(results):
    df = pd.DataFrame(results)

    # Add formatted columns
    df["Instrument"] = df["symbol"]
    df["Return"] = df["return"].apply(lambda x: f"{x:.2f} %")
    df["Max. Drawdown"] = df["maxDrawdown"].apply(lambda x: f"{x:.2f} %")
    df["Sharpe"] = df["sharpe"].apply(lambda x: f"{x:.2f}")
    df["# Trades"] = df["# trades"]
    df["Avg Trade Duration"] = df["avgTradeDuration"].astype(str)
    df["Strategy"] = df["strategy"].apply(snake_case_to_name)

    # Select relevant columns in order
    table_data = df[[
        "Instrument", "Return", "Max. Drawdown", "Sharpe", 
        "# Trades", "Avg Trade Duration", "Strategy"
    ]]

    return table_data.to_dict("records")
