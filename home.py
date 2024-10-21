from dash import Dash, dcc, html, Input, Output
import strategyTester as st
import plotly.graph_objs as go
import dataManipulator as dm
from datetime import datetime
from strategyCreator import create_strategy_creator_layout, register_callbacks  # Import new functions

app = Dash(__name__, suppress_callback_exceptions=True)

# Load all S&P 500 symbols
symbols = dm.loadSymbols('SP')

# Get current year
current_year = datetime.today().year

app.layout = html.Div([
    dcc.Tabs(id='tabs', value='backtest', children=[
        dcc.Tab(label='Backtest', value='backtest'),
        dcc.Tab(label='Strategy Creator', value='strategy_creator'),
    ]),
    html.Div(id='tabs-content')
])

# Backtest layout (your existing layout)
backtest_layout = html.Div([
    html.H1("Backtest Results"),
    dcc.Dropdown(
        id="ticker-dropdown",
        options=[{'label': symbol, 'value': symbol} for symbol in symbols],
        multi=True,
        placeholder="Select companies",
        value=['AMD'],  # Default selection
        style={'width': '100%'}
    ),
    dcc.Dropdown(
        id="strategy-dropdown",
        options=[
            {'label': 'Buy and Hold', 'value': 'buyAndHold'},
            {'label': 'Daily Range', 'value': 'dailyRange'},
            {'label': 'Solo RSI', 'value': 'soloRSI'},
            {'label': 'ROC Trend Following Bull', 'value': 'rocTrendFollowingBull'},
            {'label': 'ROC Trend Following Bear', 'value': 'rocTrendFollowingBear'},
            {'label': 'ROC Mean Reversion', 'value': 'rocMeanReversion'}
        ],
        multi=True,  # Allow multiple selections
        value=['buyAndHold'],  # Default selection
        style={'width': '100%'}
    ),
    html.Div([
        dcc.Dropdown(
            id='start-year-dropdown',
            options=[{'label': str(year), 'value': str(year)} for year in range(current_year - 10, current_year + 1)],
            value=str(current_year - 2),  # Default to 2 years ago
            style={'width': '48%', 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='end-year-dropdown',
            options=[{'label': str(year), 'value': str(year)} for year in range(current_year - 10, current_year + 1)],
            value=str(current_year),  # Default to today
            style={'width': '48%', 'display': 'inline-block'}
        ),
    ], style={'margin-top': '10px'}),
    html.Button("Run Backtest", id="run-btn", style={'margin-top': '10px', 'padding': '10px 20px', 'background-color': '#007BFF', 'color': 'white', 'border': 'none', 'border-radius': '5px', 'cursor': 'pointer'}),
    dcc.Graph(id="equity-curve"),
    html.Div(id="error-message", style={'color': 'red'})  # Error message div
])

@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_tab_content(tab):
    if tab == 'backtest':
        return backtest_layout
    elif tab == 'strategy_creator':
        return create_strategy_creator_layout()

# Register callbacks for the strategy creator
register_callbacks(app)

# Your existing callback for the backtest
@app.callback(
    Output('equity-curve', 'figure'),
    Output('error-message', 'children'),
    Input('run-btn', 'n_clicks'),
    Input('ticker-dropdown', 'value'),
    Input('strategy-dropdown', 'value'),
    Input('start-year-dropdown', 'value'),
    Input('end-year-dropdown', 'value')
)
def update_equity_curve(n_clicks, selected_symbols, selected_strategies, start_year, end_year):
    if not n_clicks or not selected_symbols:
        return go.Figure(), ""  # Empty figure and no error message

    figures = []
    error_message = ""

    # Set the start and end dates
    start_date = f"{start_year}-01-01"  # Start from January 1st of the selected start year
    end_date = f"{end_year}-12-31"  # End on December 31st of the selected end year

    for symbol in selected_symbols:
        for strategy in selected_strategies:  # Loop through selected strategies
            results = st.runBacktest(symbol, strategy, start_date, end_date)
            if results is None:
                error_message = f"No trades were made for {symbol} using {strategy}."
                continue
            
            equity_curve = results['_equity_curve']
            
            # Create a new trace for each strategy
            fig = go.Figure()
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
