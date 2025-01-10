from dash import Dash, dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import random
import pandas as pd

# Mock data for demonstration
mock_data = {
    "AAPL": pd.DataFrame({"Date": pd.date_range(start="2022-01-01", periods=100), "Open": [random.uniform(100, 200) for _ in range(100)]}),
    "GOOG": pd.DataFrame({"Date": pd.date_range(start="2022-01-01", periods=100), "Open": [random.uniform(2000, 3000) for _ in range(100)]}),
    "MSFT": pd.DataFrame({"Date": pd.date_range(start="2022-01-01", periods=100), "Open": [random.uniform(250, 350) for _ in range(100)]})
}

# Placeholder for the selected instrument and its data
training_state = {
    "instrument": None,
    "current_date_idx": 0,
    "positions": [],
    "pnl": 0
}

# Layout for the training tab
def create_training_tab_layout():
    return training_tab_layout

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
        html.Div([
            html.Button("Buy", id="buy-button"),
            html.Button("Sell", id="sell-button"),
            html.Button("Do Nothing", id="nothing-button"),
            html.Button("Next Candle", id="next-candle-button")
        ]),
        html.Div(id="pnl-display", children="PnL: $0"),
        html.Div(id="positions-log", children="Positions Log: None"),
        dcc.Graph(id="candlestick-graph", style={"height": "500px"})
    ])
])

# Callbacks for the training tab
def register_callbacks(app):
    @app.callback(
        [
            Output("training-session-controls", "style"),
            Output("training-instrument-info", "children"),
            Output("training-date-info", "children"),
            Output("pnl-display", "children"),
            Output("positions-log", "children"),
            Output("candlestick-graph", "figure")
        ],
        [
            Input("start-training-button", "n_clicks"),
            Input("buy-button", "n_clicks"),
            Input("sell-button", "n_clicks"),
            Input("nothing-button", "n_clicks"),
            Input("next-candle-button", "n_clicks")
        ],
        [
            State("training-instruments-dropdown", "value"),
            State("training-date-info", "children")
        ]
    )
    def handle_training(n_start, n_buy, n_sell, n_nothing, n_next, selected_instruments, date_info):
        ctx = callback_context
        if not ctx.triggered:
            return ({"display": "none"}, "", "", "PnL: $0", "Positions Log: None", go.Figure())

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "start-training-button" and selected_instruments:
            training_state["instrument"] = random.choice(selected_instruments)
            training_state["current_date_idx"] = 0
            training_state["positions"] = []
            training_state["pnl"] = 0

            instrument = training_state["instrument"]
            start_date = mock_data[instrument].iloc[0]["Date"]
            return (
                {"display": "block"},
                f"Trading on: {instrument}",
                f"Starting Date: {start_date}",
                "PnL: $0",
                "Positions Log: None",
                generate_candlestick_graph(instrument, 0)
            )

        instrument = training_state["instrument"]
        if not instrument:
            return ({"display": "none"}, "", date_info, f"PnL: ${training_state['pnl']}", f"Positions Log: {training_state['positions']}", go.Figure())

        if button_id in ["buy-button", "sell-button"]:
            current_data = mock_data[instrument].iloc[training_state["current_date_idx"]]
            action = "Buy" if button_id == "buy-button" else "Sell"
            quantity = 1  # Fixed for simplicity

            training_state["positions"].append({
                "type": action,
                "price": current_data["Open"],
                "quantity": quantity
            })

        if button_id == "next-candle-button":
            if training_state["current_date_idx"] < len(mock_data[instrument]) - 1:
                training_state["current_date_idx"] += 1

        # Update PnL and date info
        pnl = sum(
            (pos["price"] - mock_data[instrument].iloc[training_state["current_date_idx"]]["Open"])
            * pos["quantity"] if pos["type"] == "Sell" else
            (mock_data[instrument].iloc[training_state["current_date_idx"]]["Open"] - pos["price"]) * pos["quantity"]
            for pos in training_state["positions"]
        )
        training_state["pnl"] = pnl

        current_date = mock_data[instrument].iloc[training_state["current_date_idx"]]["Date"]

        return (
            {"display": "block"},
            f"Trading on: {instrument}",
            f"Current Date: {current_date}",
            f"PnL: ${pnl:.2f}",
            f"Positions Log: {training_state['positions']}",
            generate_candlestick_graph(instrument, training_state["current_date_idx"])
        )

def generate_candlestick_graph(instrument, current_idx):
    df = mock_data[instrument].iloc[max(0, current_idx - 99):current_idx + 1]
    fig = go.Figure(data=[go.Candlestick(
        x=df["Date"],
        open=df["Open"],
        high=df["Open"] + 5,  # Mocking high values
        low=df["Open"] - 5,   # Mocking low values
        close=df["Open"]      # Mocking close as open
    )])
    fig.update_layout(title=f"{instrument} - Last 100 Candles", xaxis_title="Date", yaxis_title="Price")
    return fig
