import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from core.screener_backend import Portfolio
import datetime as dt


def create_stock_screener_tab_layout():
    return html.Div([
        html.H3("Stock Screener", style={"textAlign": "center", "marginBottom": "20px", "color": "#FFFFFF"}),

        html.Div([
            html.Label("Select Tickers:", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id='tickers-dropdown',
                options=[{'label': ticker, 'value': ticker} for ticker in ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'AMD']],
                value=['AAPL', 'NVDA'],
                multi=True,
                placeholder="Choose tickers...",
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        html.Div([
            html.Label("Start Date:", style={"color": "#FFFFFF"}),
            dcc.DatePickerSingle(
                id='start-date-picker',
                min_date_allowed=dt.datetime(2000, 1, 1),
                max_date_allowed=dt.datetime.now(),
                initial_visible_month=dt.datetime(2024, 1, 1),
                date=dt.datetime(2024, 1, 1),
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        html.Div([
            html.Label("Days into the Future:", style={"color": "#FFFFFF"}),
            dcc.Input(
                id='timedelta-input',
                type='number',
                value=30,
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        html.Div([
            html.Label("Filter Variable:", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id='filter-variable-dropdown',
                options=[
                    {'label': 'P/E Ratio', 'value': 'pe_ratio'},
                    {'label': 'TTM Change', 'value': 'ttm_change'}
                ],
                value='pe_ratio',
                placeholder="Select filter variable...",
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        html.Div([
            html.Label("Threshold:", style={"color": "#FFFFFF"}),
            dcc.Input(
                id='threshold-input',
                type='number',
                value=10,
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        html.Div([
            html.Label("Operator:", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id='operator-dropdown',
                options=[
                    {'label': 'Greater than (>)', 'value': '>'},
                    {'label': 'Less than (<)', 'value': '<'},
                    {'label': 'Equal to (==)', 'value': '=='}
                ],
                value='>',
                placeholder="Choose operator...",
                style={"backgroundColor": "#333333", "color": "#FFFFFF"}
            ),
        ], style={"marginBottom": "20px"}),

        html.Button("Run Screener", id="run-screener-button", style={"backgroundColor": "#1E90FF", "color": "#FFFFFF", "marginTop": "10px", "fontSize": "16px", "padding": "10px 20px"}),

        html.Div([
            html.H4("Filtered Results:", style={"color": "#FFFFFF", "marginTop": "20px"}),
            html.Div(id='screener-results', style={"maxHeight": "500px", "overflowY": "auto", "backgroundColor": "#222222", "color": "#FFFFFF", "padding": "10px"})
        ])
    ], style={"backgroundColor": "#121212", "padding": "20px"})

# Define callback for filtering stocks
def register_callbacks(app):
    @app.callback(
        Output('screener-results', 'children'),
        Input('tickers-dropdown', 'value'),
        Input('start-date-picker', 'date'),
        Input('timedelta-input', 'value'),
        Input('filter-variable-dropdown', 'value'),
        Input('threshold-input', 'value'),
        Input('operator-dropdown', 'value'),
    )
    def update_screener_results(tickers, start_date, timedelta_days, variable, threshold, operator):
        if not tickers or not start_date or timedelta_days is None:
            return html.P("Please select tickers, a start date, and specify days into the future.", style={'color': 'red'})

        portfolio = Portfolio(tickers, dt.datetime.fromisoformat(start_date))
        portfolio.filter(variable, threshold, operator)
        if not portfolio.stocks:
            return html.P("No stocks match the criteria.", style={'color': 'red'})

        # Add future prices
        data = []
        for stock in portfolio.stocks:
            price_change = stock.calculate_change(timedelta_days)
            data.append({
                'Ticker': stock.ticker,
                'Price': round(stock.price, 2),
                'P/E Ratio': stock.pe_ratio,
                'TTM Change': stock.ttm_change,
                'Future Price Change': price_change or "N/A"
            })

        return dash_table.DataTable(
            data=data,
            columns=[
                {'name': 'Ticker', 'id': 'Ticker'},
                {'name': 'Price', 'id': 'Price'},
                {'name': 'P/E Ratio', 'id': 'P/E Ratio'},
                {'name': 'TTM Change', 'id': 'TTM Change'},
                {'name': 'Future Price Change', 'id': 'Future Price Change'}
            ],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center'},
            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
            style_data={'backgroundColor': '#ffffff', 'color': '#333333'},
        )
