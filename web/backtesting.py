from dash import dcc, html, Input, Output, State
from dash import dash_table
from strategies.strategy_tester import run_master_backtest, run_backtest_process, find_best_backtest, run_adaptive_backtest, load_strategies_from_json
from core.data_manipulator import load_symbols, snake_case_to_name

# Mock strategy options for demonstration
symbols = load_symbols('SP')
strategies_dict = load_strategies_from_json('strategies\strategies.json')
community_strategies_dict = load_strategies_from_json('strategies\community_strategies.json')

# Layout for the new backtesting tab
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
                    {"label": "Adaptive Strategy", "value": "adaptive_strategy"}
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

        html.Button("Run Backtest", id="run-backtest-button", style={"backgroundColor": "#1E90FF", "color": "#FFFFFF", "marginTop": "10px", "fontSize": "16px", "padding": "10px 20px"}),

        html.Div(id="backtest-results", style={"marginTop": "20px", "color": "#FFFFFF"})
    ], style={"backgroundColor": "#121212", "padding": "20px"})

# Callback for running the backtest
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

        if backtest_type != "compare_strategies" and not selected_strategy:
            return "Please select a strategy for this backtesting type."

        results = []
        if backtest_type == "compare_strategies":
            # Run compare strategies backtest
            results = run_master_backtest(instruments, selected_strategy, compare_strategies=True, plot_results=False)
            # results = [run_backtest_process(symbol, selected_strategies, False) for symbol in instruments]
        elif backtest_type == "find_best":
            # Run find best strategy backtest
            results = run_master_backtest(instruments, selected_strategy, find_best=True, plot_results=False)
        elif backtest_type == "adaptive_strategy":
            # Run adaptive strategy backtest
            results = run_master_backtest(instruments, selected_strategy, adaptive_strategy=True, plot_results=False)
        else:
            # Run normal backtest
            results = run_master_backtest(instruments, selected_strategy, plot_results=False)

        print(results)

        if not results:
            return "No results generated. Please check your selections."

        # return dash_table.DataTable(
        #     data=results,
        #     columns=[{"name": key, "id": key} for key in results[0].keys()],
        #     style_table={'overflowX': 'auto', 'backgroundColor': '#333333', 'color': '#FFFFFF'},
        #     style_header={"backgroundColor": "#444444", "color": "#FFFFFF"},
        #     style_cell={"textAlign": "center", "backgroundColor": "#222222", "color": "#FFFFFF"}
        # )
