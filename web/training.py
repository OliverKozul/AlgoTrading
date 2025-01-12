from dash import Dash, dash_table, dcc, html, Input, Output, State, callback_context
from dash_extensions import Keyboard
import random
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go

# Fetching data using yfinance
def fetch_data(ticker):
    data = yf.download(ticker, period="2y", interval="1d")
    return pd.DataFrame({
        "Date": data.index.strftime("%Y-%m-%d"),
        "Open": round(data["Open"], 4),
        "High": round(data["High"], 4),
        "Low": round(data["Low"], 4),
        "Close": round(data["Close"], 4)
    }).reset_index(drop=True)

mock_data = {
    "AAPL": fetch_data("AAPL"),
    "GOOG": fetch_data("GOOG"),
    "MSFT": fetch_data("MSFT")
}

class TradingStats:
    def __init__(self):
        self.closed_positions = []
        self.closed_pnl = 0.00
        self.open_pnl = 0.00
        self.open_positions = []

class TrainingState:
    def __init__(self):
        self.instrument = None
        self.current_date_idx = 0
        self.stats = TradingStats()

training_state = TrainingState()

# Layout for the training tab

def create_training_tab_layout():
    return training_tab_layout

training_tab_layout = html.Div([
    html.H3("Trading Skill Training", style={"textAlign": "center", "marginBottom": "20px", "color": "#FFFFFF"}),

    html.Div([
        html.Label("Select Instruments:", style={"color": "#FFFFFF"}),
        dcc.Dropdown(
            id="training-instruments-dropdown",
            options=[{"label": symbol, "value": symbol} for symbol in mock_data.keys()],
            multi=True,
            placeholder="Choose instruments...",
            style={"backgroundColor": "#333333", "color": "#FFFFFF"}
        ),
        html.Button("Start Training", id="start-training-button", style={"backgroundColor": "#1E90FF", "color": "#FFFFFF", "marginTop": "10px", "fontSize": "16px", "padding": "10px 20px"})
    ], style={"marginBottom": "20px"}),

    html.Div(id="training-session-controls", style={"display": "none", "color": "#FFFFFF"}, children=[
        html.H4("Training Session", style={"textAlign": "center"}),
        html.Div(id="training-instrument-info", style={"marginBottom": "10px"}),
        html.Div(id="training-date-info", style={"marginBottom": "10px"}),
        dcc.Graph(id="candlestick-graph", style={"height": "60vh"}),
        html.Div([
            html.Button("Buy (A)", id="buy-button", accessKey="a", style={"backgroundColor": "#32CD32", "color": "#FFFFFF", "marginRight": "10px", "fontSize": "16px", "padding": "10px 20px"}),
            html.Button("Sell (S)", id="sell-button", accessKey="s", style={"backgroundColor": "#FF4500", "color": "#FFFFFF", "marginRight": "10px", "fontSize": "16px", "padding": "10px 20px"}),
            html.Button("Next Candle (D)", id="next-candle-button", accessKey="d", style={"backgroundColor": "#1E90FF", "color": "#FFFFFF", "fontSize": "16px", "padding": "10px 20px"})
        ], style={"textAlign": "center", "marginTop": "20px", "marginBottom": "20px"}),
        html.Div(id="closed-pnl-display", children="Closed PnL: $0.00", style={"marginBottom": "10px"}),
        html.Div(id="open-pnl-display", children="Open PnL: $0.00", style={"marginBottom": "10px"}),
        html.Div([
            html.H5("Trade Log", style={"marginBottom": "10px"}),
            dash_table.DataTable(
                id="positions-table",
                columns=[
                    {"name": "Action", "id": "type"},
                    {"name": "Price", "id": "price"},
                    {"name": "Close Price", "id": "close_price"},
                    {"name": "Profit/Loss", "id": "pnl"},
                    {"name": "Quantity", "id": "quantity"},
                    {"name": "Date", "id": "date"}
                ],
                style_table={'overflowX': 'auto', 'backgroundColor': '#333333', 'color': '#FFFFFF'},
                style_header={"backgroundColor": "#444444", "color": "#FFFFFF"},
                style_cell={"textAlign": "center", "backgroundColor": "#222222", "color": "#FFFFFF"}
            ),
            html.H5("Trading Statistics", style={"marginBottom": "10px"}),
            dash_table.DataTable(
                id="trading-statistics",
                columns=[
                    {"name": "Winrate %", "id": "winrate"},
                    {"name": "Total Trades", "id": "total_trades"},
                    {"name": "Winning Trades", "id": "winning_trades"},
                    {"name": "Losing Trades", "id": "losing_trades"},
                    {"name": "Average Win", "id": "average_win"},
                    {"name": "Average Loss", "id": "average_loss"},
                    {"name": "Average Trade", "id": "average_trade"},
                    {"name": "Biggest Win", "id": "biggest_win"},
                    {"name": "Biggest Loss", "id": "biggest_loss"},
                    {"name": "Total PnL", "id": "total_pnl"},
                    {"name": "Longest Winning Streak", "id": "longest_winning_streak"},
                    {"name": "Longest Losing Streak", "id": "longest_losing_streak"}
                ],
                style_table={'overflowX': 'auto', 'backgroundColor': '#333333', 'color': '#FFFFFF'},
                style_header={"backgroundColor": "#444444", "color": "#FFFFFF"},
                style_cell={"textAlign": "center", "backgroundColor": "#222222", "color": "#FFFFFF"}
            )
        ]),
        Keyboard(id="keyboard", captureKeys=["a", "s", "d"], n_keydowns=0)
    ])
], style={"backgroundColor": "#121212", "padding": "20px"})

# Callbacks for the training tab
def register_callbacks(app):
    @app.callback(
        [
            Output("training-session-controls", "style"),
            Output("training-instrument-info", "children"),
            Output("training-date-info", "children"),
            Output("candlestick-graph", "figure"),
            Output("closed-pnl-display", "children"),
            Output("open-pnl-display", "children"),
            Output("positions-table", "data"),
            Output("trading-statistics", "data")
        ],
        [
            Input("start-training-button", "n_clicks"),
            Input("keyboard", "keydown"),
            Input("keyboard", "n_keydowns"),
            Input("buy-button", "n_clicks"),
            Input("sell-button", "n_clicks"),
            Input("next-candle-button", "n_clicks")
        ],
        [
            State("training-instruments-dropdown", "value"),
            State("training-date-info", "children")
        ]
    )
    def handle_training(n_start, key_pressed, n_keydowns, n_buy, n_sell, n_next, selected_instruments, date_info):
        key_pressed = key_pressed["key"].upper() if key_pressed else None
        ctx = callback_context
        if not ctx.triggered:
            return ({"display": "none"}, "", "", go.Figure(), "Closed PnL: $0.00", "Open PnL: $0.00", [], [])

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "start-training-button" and selected_instruments:
            training_state.instrument = random.choice(selected_instruments)
            training_state.current_date_idx = 100
            training_state.stats = TradingStats()

            instrument = training_state.instrument
            start_date = mock_data[instrument].iloc[0]["Date"]

            figure = create_candlestick_figure(mock_data[instrument], training_state.current_date_idx)

            return (
                {"display": "block"},
                f"Trading on: {instrument}",
                f"Starting Date: {start_date}",
                figure,
                "Closed PnL: $0.00",
                "Open PnL: $0.00",
                [],
                []
            )

        instrument = training_state.instrument
        if not instrument:
            return ({"display": "none"}, "", date_info, go.Figure(), f"Closed PnL: ${training_state.stats.closed_pnl}", f"Open PnL: ${training_state.stats.open_pnl}", [], [])

        if button_id in ["buy-button", "sell-button"] or key_pressed in ["A", "S"]:
            current_data = mock_data[instrument].iloc[training_state.current_date_idx]
            action = "Buy" if button_id == "buy-button" or key_pressed == "A" else "Sell"
            quantity = 1 if action == "Buy" else -1

            for pos in training_state.stats.open_positions:
                if pos["quantity"] * quantity < 0:
                    if abs(pos["quantity"]) > abs(quantity):
                        pos["quantity"] += quantity
                        partial_pos = pos.copy()
                        partial_pos["quantity"] = quantity
                        partial_pos["close_price"] = current_data["Close"]
                        partial_pos["pnl"] = round((partial_pos["close_price"] - pos["price"]) * partial_pos["quantity"], 2)
                        training_state.stats.closed_positions.insert(0, pos)
                        quantity = 0
                    else:
                        quantity += pos["quantity"]
                        pos["close_price"] = current_data["Close"]
                        pos["pnl"] = round((pos["close_price"] - pos["price"]) * pos["quantity"], 2)
                        training_state.stats.closed_positions.insert(0, pos)
                        training_state.stats.closed_pnl += pos["pnl"]
                        training_state.stats.open_positions.remove(pos)
            
            if quantity != 0:
                training_state.stats.open_positions.append({"type": action, "price": current_data["Close"], "close_price": None, "pnl": None, "quantity": quantity, "date": current_data["Date"]})

        if button_id == "next-candle-button" or key_pressed == "D":
            if training_state.current_date_idx < len(mock_data[instrument]) - 1:
                training_state.current_date_idx += 1

        current_price = mock_data[instrument].iloc[training_state.current_date_idx]["Close"]
        current_date = mock_data[instrument].iloc[training_state.current_date_idx]["Date"]
        training_state.stats.open_pnl = sum([pos["quantity"] * (current_price - pos["price"]) for pos in training_state.stats.open_positions])
        figure = create_candlestick_figure(mock_data[instrument], training_state.current_date_idx)
        closed_pnl = training_state.stats.closed_pnl
        open_pnl = training_state.stats.open_pnl
        # Calculate additional statistics
        total_trades = len(training_state.stats.closed_positions)
        winning_trades = len([pos for pos in training_state.stats.closed_positions if pos["pnl"] > 0])
        winrate = (winning_trades / total_trades) * 100 if total_trades else 0
        losing_trades = len([pos for pos in training_state.stats.closed_positions if pos["pnl"] <= 0])
        average_win = sum([pos["pnl"] for pos in training_state.stats.closed_positions if pos["pnl"] > 0]) / winning_trades if winning_trades else 0
        average_loss = sum([pos["pnl"] for pos in training_state.stats.closed_positions if pos["pnl"] <= 0]) / losing_trades if losing_trades else 0
        average_trade = sum([pos["pnl"] for pos in training_state.stats.closed_positions]) / total_trades if total_trades else 0
        biggest_win = max([pos["pnl"] for pos in training_state.stats.closed_positions], default=0)
        biggest_loss = min([pos["pnl"] if pos["pnl"] <= 0 else 0 for pos in training_state.stats.closed_positions], default=0)
        total_pnl = closed_pnl + open_pnl
        longest_winning_streak = 0
        longest_losing_streak = 0
        current_streak = 0

        for pos in training_state.stats.closed_positions:
            if pos["pnl"] > 0:
                if current_streak >= 0:
                    current_streak += 1
                else:
                    current_streak = 1
            else:
                if current_streak <= 0:
                    current_streak -= 1
                else:
                    current_streak = -1
            longest_winning_streak = max(longest_winning_streak, current_streak)
            longest_losing_streak = abs(min(longest_losing_streak, current_streak))

        return (
            {"display": "block"},
            f"Trading on: {instrument}",
            f"Current Date: {current_date}",
            figure,
            f"Closed PnL: ${closed_pnl:.2f}",
            f"Open PnL: ${open_pnl:.2f}",
            training_state.stats.closed_positions,
            [{
                "winrate": f"{winrate:.2f}%",
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "average_win": f"${average_win:.2f}",
                "average_loss": f"${average_loss:.2f}",
                "average_trade": f"${average_trade:.2f}",
                "biggest_win": f"${biggest_win:.2f}",
                "biggest_loss": f"${biggest_loss:.2f}",
                "total_pnl": f"${total_pnl:.2f}",
                "longest_winning_streak": longest_winning_streak,
                "longest_losing_streak": longest_losing_streak
            }]
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
                close=plot_data["Close"],
                increasing_line_color="green",
                decreasing_line_color="red",
                whiskerwidth=0.2
            )
        ]
    )

    # Add average price line
    price_sum = 0
    quantity_sum = 0
    for pos in training_state.stats.open_positions:
        price_sum += pos["price"] * pos["quantity"]
        quantity_sum += pos["quantity"]

    avg_price = price_sum / quantity_sum if quantity_sum else 0

    if training_state.stats.open_positions:
        color = "green" if quantity_sum > 0 else "red"
        figure.add_shape(
            type="line",
            x0=plot_data["Date"].iloc[0],
            x1=plot_data["Date"].iloc[-1],
            y0=avg_price,
            y1=avg_price,
            line=dict(color=color, width=2, dash="dash")
        )

    # Update layout to mimic TradingView style
    figure.update_layout(
        title="Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        plot_bgcolor="#1E1E1E",
        paper_bgcolor="#1E1E1E",
        font=dict(color="white"),
        xaxis=dict(
            gridcolor="#444444",
            showline=True,
            linewidth=1,
            linecolor="#888888",
        ),
        yaxis=dict(
            gridcolor="#444444",
            showline=True,
            linewidth=1,
            linecolor="#888888",
        ),
    )

    return figure