from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go
from core.data_manipulator import load_symbols, snake_case_to_name
from strategies.strategy_tester import run_backtest, load_strategies_from_json
from datetime import datetime
import web.backtesting as backtesting
import web.strategy_creator as strategy_creator
import web.pnl_calculator as pnl_calculator
import web.training as training


app = Dash("Cool", suppress_callback_exceptions=True)

# Load all S&P 500 symbols
symbols = load_symbols('SP')
strategies_dict = load_strategies_from_json('strategies\strategies.json')
community_strategies_dict = load_strategies_from_json('strategies\community_strategies.json')

# Get current year
last_year = datetime.today().year - 1

app.layout = html.Div([
    dcc.Tabs(id='tabs', value='home', children=[
        dcc.Tab(label='Visualize Backtests', value='home'),
        dcc.Tab(label='Backtest', value='backtest'),
        dcc.Tab(label='Strategy Creator', value='strategy_creator'),
        dcc.Tab(label="P&L Calculator", value='pnl_calculator'),
        dcc.Tab(label="Training", value='training')
    ]),
    html.Div(id='tabs-content')
])

def create_home_tab_layout():
    return html.Div([
        html.H3("Backtest Results", style={"textAlign": "center", "marginBottom": "20px", "color": "#FFFFFF"}),

        # Ticker Selection
        html.Div([
            html.Label("Select Companies:", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id="ticker-dropdown",
                options=[{'label': symbol, 'value': symbol} for symbol in symbols],
                multi=True,
                placeholder="Select companies",
                value=['AMD'],  # Default selection
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        # Official Strategies
        html.Div([
            html.H3("Official Strategies", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id="strategy-dropdown-official",
                options=[
                    {'label': snake_case_to_name(key), 'value': key}
                    for key in strategies_dict.keys()
                ],
                multi=True,  # Allow multiple selections
                value=['Buy_And_Hold'],  # Default selection
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        # Community Strategies
        html.Div([
            html.H3("Community Strategies", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id="strategy-dropdown-community",
                options=[
                    {'label': snake_case_to_name(key), 'value': key}
                    for key in community_strategies_dict.keys()
                ],
                multi=True,  # Allow multiple selections
                value=[],  # No default selection
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        # Date Range Selection
        html.Div([
            html.Label("Select Date Range:", style={"color": "#FFFFFF"}),
            html.Div([
                dcc.Dropdown(
                    id='start-year-dropdown',
                    options=[{'label': str(year), 'value': str(year)} for year in range(last_year - 10, last_year + 1)],
                    value=str(last_year - 2),  # Default to 2 years ago
                    style={"width": "48%", "display": "inline-block", "backgroundColor": "#333333", "color": "#FFFFFF"}
                ),
                dcc.Dropdown(
                    id='end-year-dropdown',
                    options=[{'label': str(year), 'value': str(year)} for year in range(last_year - 10, last_year + 1)],
                    value=str(last_year),  # Default to today
                    style={"width": "48%", "display": "inline-block", "backgroundColor": "#333333", "color": "#FFFFFF"}
                ),
            ]),
        ], style={"marginBottom": "20px"}),

        # Run Backtest Button
        html.Button(
            "Run Backtest",
            id="run-btn",
            style={
                "backgroundColor": "#1E90FF",
                "color": "#FFFFFF",
                "fontSize": "16px",
                "padding": "10px 20px",
                "border": "none",
                "cursor": "pointer",
                "marginTop": "10px"
            },
        ),

        # Equity Curve Plot
        html.Div([
            html.Label("Equity Curve:", style={"color": "#FFFFFF"}),
            dcc.Graph(
                id="equity-curve",
                style={"backgroundColor": "#333333"}
            ),
        ], style={"marginTop": "20px"}),

        # Error Message
        html.Div(id="error-message", style={"color": "red", "marginTop": "20px"}),
    ], style={"backgroundColor": "#121212", "padding": "20px"})

@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_tab_content(tab):
    if tab == 'home':
        return create_home_tab_layout()
    elif tab == 'backtest':
        return backtesting.create_backtesting_tab_layout()
    elif tab == 'strategy_creator':
        return strategy_creator.create_strategy_creator_tab_layout()
    elif tab == 'pnl_calculator':
        return pnl_calculator.create_pnl_calculator_tab_layout()
    elif tab == 'training':
        return training.create_training_tab_layout()

# Register callbacks
backtesting.register_callbacks(app)
strategy_creator.register_callbacks(app)
pnl_calculator.register_callbacks(app)
training.register_callbacks(app)

# Your existing callback for the backtest
@app.callback(
    Output('equity-curve', 'figure'),
    Output('error-message', 'children'),
    Input('run-btn', 'n_clicks'),
    Input('ticker-dropdown', 'value'),
    Input('strategy-dropdown-official', 'value'),
    Input('strategy-dropdown-community', 'value'),
    Input('start-year-dropdown', 'value'),
    Input('end-year-dropdown', 'value')
)
def update_equity_curve(n_clicks, selected_symbols, official_strategies, community_strategies, start_year, end_year):
    if not n_clicks or not selected_symbols:
        return go.Figure(), ""  # Empty figure and no error message

    figures = []
    error_message = ""

    # Combine selected official and community strategies
    selected_strategies = (official_strategies or []) + (community_strategies or [])

    # Set the start and end dates
    start_date = f"{start_year}-01-01"  # Start from January 1st of the selected start year
    end_date = f"{end_year}-12-31"  # End on December 31st of the selected end year

    for symbol in selected_symbols:
        for strategy in selected_strategies:  # Loop through selected strategies
            results = run_backtest(symbol, strategy, False, start_date, end_date)
            if results is None:
                error_message = f"No trades were made for {symbol} using {strategy}."
                continue
            
            equity_curve = results['_equity_curve']
            
            # Create a new trace for each strategy
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[equity_curve.index[0], equity_curve.index[-1]], y=[100000, 100000], mode='lines', name=f'Baseline 100 000'))
            fig.add_trace(go.Scatter(x=equity_curve.index, y=equity_curve['Equity'], mode='lines', name=f'{strategy} - {symbol}'))
            figures.append(fig)

    if figures:
        combined_fig = figures[0]  # Start with the first figure
        for fig in figures[1:]:
            combined_fig.add_traces(fig.data)  # Combine traces from other figures

        return combined_fig, error_message

    return go.Figure(), error_message  # Return empty figure and error message if no tickers were processed


if __name__ == '__main__':
    app.run_server(debug=True)
