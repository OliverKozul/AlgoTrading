from dash import Dash, dash_table, dcc, html, Input, Output, State, callback_context
import random
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go

# Fetching data using yfinance
def fetch_data(ticker):
    data = yf.download(ticker, period="2y", interval="1d")
    return pd.DataFrame({"Date": data.index, "Open": round(data["Open"], 4), "High": round(data["High"], 4), "Low": round(data["Low"], 4), "Close": round(data["Close"], 4)}).reset_index(drop=True)

mock_data = {
    "AAPL": fetch_data("AAPL"),
    "GOOG": fetch_data("GOOG"),
    "MSFT": fetch_data("MSFT")
}

# Placeholder for the selected instrument and its data
def create_training_tab_layout():
    return training_tab_layout
  
training_state = {
    "instrument": None,
    "current_date_idx": 0,
    "positions": [],
    "pnl": 0
}

# Layout for the training tab
training_tab_layout = html.Div([
    html.H3("Trading Skill Training"),

    html.Div([
        html.Label("Select Instruments:"),
        dcc.Dropdown(
            id="training-instruments-dropdown",
            options=[{"label": symbol, "value": symbol} for symbol in mock_data.keys()],
            multi=True
        ),
        html.Button("Start Training", id="start-training-button")
    ]),

    html.Div(id="training-session-controls", style={"display": "none"}, children=[
        html.H4("Training Session"),
        html.Div(id="training-instrument-info"),
        html.Div(id="training-date-info"),
        dcc.Graph(id="candlestick-graph"),
        html.Div([
            html.Button("Buy", id="buy-button"),
            html.Button("Sell", id="sell-button"),
            html.Button("Next Candle", id="next-candle-button")
        ]),
        html.Div(id="pnl-display", children="PnL: $0"),
        html.Div([
            html.H5("Trade Log"),
            dash_table.DataTable(
                id="positions-table",
                columns=[
                    {"name": "Action", "id": "action"},
                    {"name": "Price", "id": "price"},
                    {"name": "Quantity", "id": "quantity"},
                    {"name": "Date", "id": "date"}
                ]
            )
        ])
    ])
])

# Callbacks for the training tab
def register_callbacks(app):
    @app.callback(
        [
            Output("training-session-controls", "style"),
            Output("training-instrument-info", "children"),
            Output("training-date-info", "children"),
            Output("candlestick-graph", "figure"),
            Output("pnl-display", "children"),
            Output("positions-table", "data")
        ],
        [
            Input("start-training-button", "n_clicks"),
            Input("buy-button", "n_clicks"),
            Input("sell-button", "n_clicks"),
            Input("next-candle-button", "n_clicks")
        ],
        [
            State("training-instruments-dropdown", "value"),
            State("training-date-info", "children")
        ]
    )
    def handle_training(n_start, n_buy, n_sell, n_next, selected_instruments, date_info):
        ctx = callback_context
        if not ctx.triggered:
            return ({"display": "none"}, "", "", go.Figure(), "PnL: $0", [])

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "start-training-button" and selected_instruments:
            training_state["instrument"] = random.choice(selected_instruments)
            training_state["current_date_idx"] = 100
            training_state["positions"] = []
            training_state["pnl"] = 0

            instrument = training_state["instrument"]
            start_date = mock_data[instrument].iloc[0]["Date"]

            figure = create_candlestick_figure(mock_data[instrument], training_state["current_date_idx"])

            return (
                {"display": "block"},
                f"Trading on: {instrument}",
                f"Starting Date: {start_date}",
                figure,
                "PnL: $0",
                []
            )

        instrument = training_state["instrument"]
        if not instrument:
            return ({"display": "none"}, "", date_info, go.Figure(), f"PnL: ${training_state['pnl']}", [])

        if button_id in ["buy-button", "sell-button"]:
            current_data = mock_data[instrument].iloc[training_state["current_date_idx"]]
            action = "Buy" if button_id == "buy-button" else "Sell"
            quantity = 1  # Fixed for simplicity

            training_state["positions"].append({
                "type": action,
                "price": current_data["Close"],
                "quantity": quantity,
                "date": current_data["Date"]
            })

        if button_id == "next-candle-button":
            if training_state["current_date_idx"] < len(mock_data[instrument]) - 1:
                training_state["current_date_idx"] += 1

        # Update PnL and date info
        pnl = sum(
            (pos["price"] - mock_data[instrument].iloc[training_state["current_date_idx"]]["Close"])
            * pos["quantity"] if pos["type"] == "Sell" else
            (mock_data[instrument].iloc[training_state["current_date_idx"]]["Close"] - pos["price"]) * pos["quantity"]
            for pos in training_state["positions"]
        )
        training_state["pnl"] = pnl

        current_date = mock_data[instrument].iloc[training_state["current_date_idx"]]["Date"]

        figure = create_candlestick_figure(mock_data[instrument], training_state["current_date_idx"])

        positions_data = [
            {
                "action": pos["type"],
                "price": pos["price"],
                "quantity": pos["quantity"],
                "date": pos["date"]
            }
            for pos in training_state["positions"]
        ]

        return (
            {"display": "block"},
            f"Trading on: {instrument}",
            f"Current Date: {current_date}",
            figure,
            f"PnL: ${pnl:.2f}",
            positions_data
        )

def create_candlestick_figure(data, current_idx):
    start_idx = max(0, current_idx - 99)
    plot_data = data.iloc[start_idx:current_idx + 1]

    figure = go.Figure(
        data=[
            go.Candlestick(
                x=plot_data["Date"],
                open=plot_data["Open"], 
                high=plot_data["High"], 
                low=plot_data["Low"], 
                close=plot_data["Close"]
            )
        ]
    )

    # Add buy/sell markers
    price_sum_sell = 0
    quantity_sum_sell = 0
    price_sum_buy = 0
    quantity_sum_buy = 0
    for pos in training_state["positions"]:
        if pos["type"] == "Sell":
            price_sum_sell += pos["price"] * pos["quantity"]
            quantity_sum_sell += pos["quantity"]
        else:
            price_sum_buy += pos["price"] * pos["quantity"]
            quantity_sum_buy += pos["quantity"]

    price_sum = price_sum_buy - price_sum_sell
    quantity_sum = quantity_sum_buy - quantity_sum_sell

    if quantity_sum != 0:
        print(price_sum, quantity_sum)
        color = "green" if quantity_sum > 0 else "red"
        figure.add_shape(
            type="line",
            x0=plot_data["Date"].iloc[0],
            x1=plot_data["Date"].iloc[-1],
            y0=abs(price_sum / quantity_sum),
            y1=abs(price_sum / quantity_sum),
            line=dict(color=color)
        )

    figure.update_layout(title="Past 100 Candles", xaxis_title="Date", yaxis_title="Price")
    return figure
