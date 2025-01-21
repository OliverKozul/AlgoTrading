from dash import dash_table, dcc, html, Input, Output, State, callback_context
from dash_extensions import Keyboard
from core.data_manipulator import fetch_data, load_symbols
from web.utils import apply_dark_theme
import random
import pandas as pd
import datetime
import plotly.graph_objs as go
from typing import List, Tuple, Dict, Any


stock_data = {symbol: None for symbol in load_symbols('SP')}

class TradingStats:
    def __init__(self):
        self.closed_positions: List[Dict[str, Any]] = []
        self.closed_pnl: float = 0.00
        self.open_pnl: float = 0.00
        self.open_positions: List[Dict[str, Any]] = []
        self.open_quantity: int = 0

class TrainingState:
    def __init__(self):
        self.instrument: str = None
        self.current_date_idx: int = 0
        self.stats: TradingStats = TradingStats()

training_state = TrainingState()

def create_training_tab_layout() -> html.Div:
    return html.Div([
        html.H3("Trading Skill Training", style={"textAlign": "center", "marginBottom": "20px", "color": "#FFFFFF"}),

        html.Div([
            html.Label("Select Instruments:", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id="training-instruments-dropdown",
                options=[{"label": symbol, "value": symbol} for symbol in stock_data.keys()],
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
            html.Div(id="open-quantity-display", children="Open Quantity: 0", style={"marginBottom": "10px"}),
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
                        {"name": "Open Date", "id": "open_date"},
                        {"name": "Close Date", "id": "close_date"}
                    ],
                    style_table={'overflowX': 'auto', 'backgroundColor': '#333333', 'color': '#FFFFFF'},
                    style_header={"backgroundColor": "#444444", "color": "#FFFFFF"},
                    style_cell={"textAlign": "center", "backgroundColor": "#222222", "color": "#FFFFFF"}
                ),
                html.H5("Trading Statistics", style={"marginBottom": "10px"}),
                dash_table.DataTable(
                    id="trading-statistics",
                    columns=[
                        {"name": "Total PnL", "id": "total_pnl"},
                        {"name": "Winrate %", "id": "winrate"},
                        {"name": "Total Trades", "id": "total_trades"},
                        {"name": "Winning Trades", "id": "winning_trades"},
                        {"name": "Losing Trades", "id": "losing_trades"},
                        {"name": "Sharpe Ratio", "id": "sharpe_ratio"},
                        {"name": "Average Win", "id": "average_win"},
                        {"name": "Average Loss", "id": "average_loss"},
                        {"name": "Average Trade", "id": "average_trade"},
                        {"name": "Biggest Win", "id": "biggest_win"},
                        {"name": "Biggest Loss", "id": "biggest_loss"},
                        {"name": "Longest Winning Streak", "id": "longest_winning_streak"},
                        {"name": "Longest Losing Streak", "id": "longest_losing_streak"}
                    ],
                    style_table={'overflowX': 'auto', 'backgroundColor': '#333333', 'color': '#FFFFFF'},
                    style_header={"backgroundColor": "#444444", "color": "#FFFFFF"},
                    style_cell={"textAlign": "center", "backgroundColor": "#222222", "color": "#FFFFFF"}
                )
            ]),
            html.Div([
                dcc.Graph(id="pnl-graph-training", style={"height": "40vh"})
            ], style={"marginTop": "20px"}),
            Keyboard(id="keyboard", captureKeys=["a", "s", "d"], n_keydowns=0)
        ]),
    ], style={"backgroundColor": "#121212", "padding": "20px"})

def register_callbacks(app) -> None:
    @app.callback(
        [
            Output("training-session-controls", "style"),
            Output("training-instrument-info", "children"),
            Output("training-date-info", "children"),
            Output("candlestick-graph", "figure"),
            Output("pnl-graph-training", "figure"),
            Output("closed-pnl-display", "children"),
            Output("open-pnl-display", "children"),
            Output("open-quantity-display", "children"),
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
    def handle_training(n_start: int, key_pressed: Dict[str, Any], n_keydowns: int, n_buy: int, n_sell: int, n_next: int, selected_instruments: List[str], date_info: str) -> Tuple[Dict[str, str], str, str, go.Figure, go.Figure, str, str, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        key_pressed = key_pressed["key"].upper() if key_pressed else None
        ctx = callback_context
        if not ctx.triggered:
            return ({"display": "none"}, "", "", go.Figure(), go.Figure(), "Closed PnL: $0.00", "Open PnL: $0.00", "Open Quantity: 0", [], [])

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "start-training-button" and selected_instruments:
            handle_start_training(selected_instruments)

        instrument = training_state.instrument

        if not instrument:
            return ({"display": "none"}, "", date_info, go.Figure(), go.Figure(), f"Closed PnL: ${training_state.stats.closed_pnl}", f"Open PnL: ${training_state.stats.open_pnl}", f"Open Quantity: {training_state.stats.open_quantity}", [], [])
        if button_id in ["buy-button", "sell-button"] or key_pressed in ["A", "S"]:
            handle_buy_sell(instrument, button_id, key_pressed)
        if button_id == "next-candle-button" or key_pressed == "D":
            if training_state.current_date_idx < len(stock_data[instrument]) - 1:
                training_state.current_date_idx += 1

        return calculate_stats(instrument)

def handle_start_training(selected_instruments: List[str]) -> Tuple[Dict[str, str], str, str, go.Figure, go.Figure, str, str, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    training_state.instrument = random.choice(selected_instruments)
    start_date = (datetime.datetime.now() - datetime.timedelta(days=random.randint(2*365, 10*365))).strftime("%Y-%m-%d")
    stock_data[training_state.instrument] = fetch_data(training_state.instrument, start_date)
    stock_data[training_state.instrument]["Close"] = round(stock_data[training_state.instrument]["Close"], 4)
    stock_data[training_state.instrument]["Date"] = stock_data[training_state.instrument]["Date"].dt.strftime("%Y-%m-%d")
    training_state.current_date_idx = 100
    training_state.stats = TradingStats()

    instrument = training_state.instrument
    start_date = stock_data[instrument].iloc[0]["Date"]

    candle_fig = create_candlestick_figure(stock_data[instrument], training_state.current_date_idx)
    pnl_fig = create_pnl_graph(instrument)

    return (
        {"display": "block"},
        f"Trading on: {instrument}",
        f"Starting Date: {start_date}",
        candle_fig,
        pnl_fig,
        "Closed PnL: $0.00",
        "Open PnL: $0.00",
        "Open Quantity: 0",
        [],
        []
    )

def handle_buy_sell(instrument: str, button_id: str, key_pressed: str) -> None:
    current_data = stock_data[instrument].iloc[training_state.current_date_idx]
    action = "Buy" if button_id == "buy-button" or key_pressed == "A" else "Sell"
    quantity = 1 if action == "Buy" else -1
    training_state.stats.open_quantity += quantity

    for pos in training_state.stats.open_positions:
        if pos["quantity"] * quantity < 0:
            if abs(pos["quantity"]) > abs(quantity):
                pos["quantity"] += quantity
                partial_pos = pos.copy()
                partial_pos["quantity"] = quantity
                partial_pos["close_price"] = current_data["Close"]
                partial_pos["close_date"] = current_data["Date"]
                partial_pos["pnl"] = round((partial_pos["close_price"] - pos["price"]) * partial_pos["quantity"], 2)
                training_state.stats.closed_positions.insert(0, pos)
                quantity = 0
            else:
                quantity += pos["quantity"]
                pos["close_price"] = current_data["Close"]
                pos["close_date"] = current_data["Date"]
                pos["pnl"] = round((pos["close_price"] - pos["price"]) * pos["quantity"], 2)
                training_state.stats.closed_positions.insert(0, pos)
                training_state.stats.closed_pnl += pos["pnl"]
                training_state.stats.open_positions.remove(pos)
    
    if quantity != 0:
        training_state.stats.open_positions.append({"type": action, "price": current_data["Close"], "close_price": None, "pnl": None, "quantity": quantity, "open_date": current_data["Date"], "close_date": None})

def create_candlestick_figure(data: pd.DataFrame, current_idx: int) -> go.Figure:
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

    figure.update_layout(
        title="Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False
    )
    apply_dark_theme(figure)

    return figure

def create_pnl_graph(instrument: str) -> go.Figure:
    pnl_data = []
    closed_positions = training_state.stats.closed_positions[::-1]

    dates = []
    buy_and_hold_data = []
    initial_price = stock_data[instrument].iloc[100]["Close"]

    for i in range(100, training_state.current_date_idx + 1):
        current_pnl = 0
        for pos in closed_positions:
            current_pnl += pos["pnl"] if pos["close_date"] <= stock_data[instrument].iloc[i]["Date"] else 0
        current_price = stock_data[instrument].iloc[i]["Close"]
        dates.append(stock_data[instrument].iloc[i]["Date"])
        buy_and_hold_data.append(current_price - initial_price)
        pnl_data.append(current_pnl)
        
    figure = go.Figure(
        data=[
            go.Scatter(
                x=dates,
                y=pnl_data,
                mode="lines+markers",
                marker=dict(color="blue"),
                name="PnL"
            ),
            go.Scatter(
                x=dates,
                y=buy_and_hold_data,
                mode="lines+markers",
                marker=dict(color="orange"),
                name="Buy and Hold"
            )
        ]
    )

    figure.update_layout(
        title="PnL Graph",
        xaxis_title="Date",
        yaxis_title="PnL",
        xaxis_rangeslider_visible=False
    )
    apply_dark_theme(figure)

    return figure

def calculate_streaks() -> Tuple[int, int]:
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

    return longest_winning_streak, longest_losing_streak

def calculate_sharpe_ratio() -> float:
    returns = [pos["pnl"] / 100 for pos in training_state.stats.closed_positions]

    return 0 if len(returns) == 0 else (sum(returns) / len(returns)) / (pd.Series(returns).std() * (252 ** 0.5))

def calculate_stats(instrument: str) -> Tuple[Dict[str, str], str, str, go.Figure, go.Figure, str, str, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    current_price = stock_data[instrument].iloc[training_state.current_date_idx]["Close"]
    current_date = stock_data[instrument].iloc[training_state.current_date_idx]["Date"]
    training_state.stats.open_pnl = sum([pos["quantity"] * (current_price - pos["price"]) for pos in training_state.stats.open_positions])
    candle_fig = create_candlestick_figure(stock_data[instrument], training_state.current_date_idx)
    pnl_fig = create_pnl_graph(instrument)
    closed_pnl = training_state.stats.closed_pnl
    open_pnl = training_state.stats.open_pnl
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
    sharpe = calculate_sharpe_ratio()
    longest_winning_streak, longest_losing_streak = calculate_streaks() 

    return (
        {"display": "block"},
        f"Trading on: {instrument}",
        f"Current Date: {current_date}",
        candle_fig,
        pnl_fig,
        f"Closed PnL: ${closed_pnl:.2f}",
        f"Open PnL: ${open_pnl:.2f}",
        f"Open Quantity: {training_state.stats.open_quantity}",
        training_state.stats.closed_positions,
        [{
            "total_pnl": f"${total_pnl:.2f}",
            "winrate": f"{winrate:.2f}%",
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "sharpe_ratio": f"{sharpe:.2f}",
            "average_win": f"${average_win:.2f}",
            "average_loss": f"${average_loss:.2f}",
            "average_trade": f"${average_trade:.2f}",
            "biggest_win": f"${biggest_win:.2f}",
            "biggest_loss": f"${biggest_loss:.2f}",
            "longest_winning_streak": longest_winning_streak,
            "longest_losing_streak": longest_losing_streak
        }]
    )
