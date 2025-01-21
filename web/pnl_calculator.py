from dash import Dash, dcc, html, Input, Output, State, ctx, ALL
from dash.exceptions import PreventUpdate
from web.utils import apply_dark_theme
import core.data_manipulator as dm
import numpy as np
import plotly.graph_objects as go
from typing import List, Dict, Any, Union, Tuple


symbols = dm.load_symbols('SP')

def create_pnl_calculator_tab_layout() -> html.Div:
    return html.Div([
        html.H3("P&L Calculator", style={"textAlign": "center", "marginBottom": "20px", "color": "#FFFFFF"}),

        # Symbol Selection
        html.Div([
            html.Label("Select Symbol:", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id="symbol-dropdown",
                options=symbols,
                value="AAPL",
                placeholder="Select a symbol",
                style={
                    "width": "100%", 
                    "backgroundColor": "#333333", 
                    "color": "#FFFFFF"
                }
            ),
        ], style={"marginBottom": "20px"}),

        # Position Type Selection
        html.Div([
            html.Label("Position Type:", style={"color": "#FFFFFF"}),
            dcc.Dropdown(
                id="position-type",
                options=[
                    {"label": "Stock", "value": "stock"},
                    {"label": "Buy Call", "value": "buy_call"},
                    {"label": "Sell Call", "value": "sell_call"},
                    {"label": "Buy Put", "value": "buy_put"},
                    {"label": "Sell Put", "value": "sell_put"}
                ],
                placeholder="Select position type",
                style={
                    "width": "100%", 
                    "backgroundColor": "#333333", 
                    "color": "#FFFFFF"
                }
            ),
        ], style={"marginBottom": "20px"}),

        # Dynamic Position Inputs
        html.Div(id="position-inputs", style={"marginBottom": "20px"}),

        # Add Position Button
        html.Button(
            "Add Position",
            id="add-position-btn",
            style={
                "backgroundColor": "#1E90FF",
                "color": "#FFFFFF",
                "fontSize": "16px",
                "padding": "10px 20px",
                "border": "none",
                "cursor": "pointer",
                "marginTop": "10px",
                "width": "100%"
            },
        ),

        # Separator
        html.Hr(style={"borderColor": "#555555"}),

        # Positions List
        html.Div(
            id="positions-list", 
            style={
                "marginTop": "20px", 
                "padding": "10px", 
                "backgroundColor": "#333333", 
                "color": "#FFFFFF", 
                "border": "1px solid #555555"
            }
        ),

        # Separator
        html.Hr(style={"borderColor": "#555555"}),

        # P&L Graph
        dcc.Graph(
            id="pnl-graph",
            style={
                "backgroundColor": "#121212", 
                "border": "1px solid #555555"
            }
        ),

        # Hidden Store for Positions Data
        dcc.Store(id="positions-data", data=[])
    ], style={"backgroundColor": "#121212", "padding": "20px"})

def register_callbacks(app: Dash) -> None:
    @app.callback(
        Output("position-inputs", "children"),
        Input("position-type", "value"),
    )
    def update_position_inputs(position_type: str) -> html.Div:
        disabled_states = {
            "stock": {"buy-price": False, "strike-price": True, "premium": True, "position-quantity": False},
            "buy_call": {"buy-price": True, "strike-price": False, "premium": False, "position-quantity": False},
            "buy_put": {"buy-price": True, "strike-price": False, "premium": False, "position-quantity": False},
            "sell_call": {"buy-price": True, "strike-price": False, "premium": False, "position-quantity": False},
            "sell_put": {"buy-price": True, "strike-price": False, "premium": False, "position-quantity": False},
        }

        state = disabled_states.get(position_type, {"buy-price": True, "strike-price": True, "premium": True, "position-quantity": True})

        return html.Div([
            html.Label("Buy Price:"),
            dcc.Input(
                id="buy-price",
                type="number",
                placeholder="Enter buy price",
                style={"width": "100%"},
                disabled=state["buy-price"]
            ),
            html.Label("Strike Price:"),
            dcc.Input(
                id="strike-price",
                type="number",
                placeholder="Enter strike price",
                style={"width": "100%"},
                disabled=state["strike-price"]
            ),
            html.Label("Premium:"),
            dcc.Input(
                id="premium",
                type="number",
                placeholder="Enter premium",
                style={"width": "100%"},
                disabled=state["premium"]
            ),
            html.Label("Quantity:"),
            dcc.Input(
                id="position-quantity",
                type="number",
                placeholder="Enter quantity",
                style={"width": "100%"},
                disabled=state["position-quantity"]
            ),
        ])

    @app.callback(
        Output("positions-data", "data"),
        Output("positions-list", "children"),
        Input("add-position-btn", "n_clicks"),
        Input({'type': 'remove-btn', 'index': ALL}, "n_clicks"),
        State("positions-data", "data"),
        State("position-type", "value"),
        State("buy-price", "value"),
        State("strike-price", "value"),
        State("premium", "value"),
        State("position-quantity", "value"),
        prevent_initial_call=True
    )
    def modify_positions(add_click: int, remove_clicks: List[int], positions: List[Dict[str, Any]], position_type: str, buy_price: Union[float, None], strike_price: Union[float, None], premium: Union[float, None], quantity: Union[int, None]) -> Tuple[List[Dict[str, Any]], List[html.Div]]:
        triggered = ctx.triggered_id

        if not positions:
            positions = []

        if triggered == "add-position-btn":
            if not position_type or quantity is None or quantity <= 0:
                raise PreventUpdate

            if position_type == "stock" and buy_price is None:
                raise PreventUpdate
            elif position_type != "stock" and (strike_price is None or premium is None):
                raise PreventUpdate

            new_position = {
                "type": position_type,
                "buy_price": buy_price if position_type == "stock" else None,
                "strike_price": strike_price if position_type != "stock" else None,
                "premium": premium if position_type != "stock" else None,
                "quantity": quantity
            }
            positions.append(new_position)

        elif isinstance(triggered, dict) and triggered["type"] == "remove-btn":
            index_to_remove = triggered["index"]
            if index_to_remove < len(positions):
                positions.pop(index_to_remove)

        positions_list = [
            html.Div([
                f"Type: {p['type']}, ",
                f"Buy Price: {p.get('buy_price', 'N/A')}, ",
                f"Strike Price: {p.get('strike_price', 'N/A')}, ",
                f"Premium: {p.get('premium', 'N/A')}, ",
                f"Quantity: {p['quantity']}",
                html.Button("Remove", id={'type': 'remove-btn', 'index': i}, style={'margin-left': '10px'})
            ]) for i, p in enumerate(positions)
        ]
        return positions, positions_list

    @app.callback(
        Output("pnl-graph", "figure"),
        Input("positions-data", "data"),
        Input("symbol-dropdown", "value"),
    )
    def update_pnl_graph(positions: List[Dict[str, Any]], symbol: str) -> go.Figure:
        if not positions:
            figure = go.Figure()
            apply_dark_theme(figure)
            return figure

        min_price_in_positions = min(
            [pos["buy_price"] if pos["type"] == "stock" else pos["strike_price"] for pos in positions]
        )
        max_price_in_positions = max(
            [pos["buy_price"] if pos["type"] == "stock" else pos["strike_price"] for pos in positions]
        )
        price_range = np.linspace(0.9 * min_price_in_positions, 1.1 * max_price_in_positions, 500)
        total_pnl = np.zeros_like(price_range)

        for position in positions:
            if position["type"] == "stock":
                total_pnl += (price_range - position["buy_price"]) * position["quantity"]
            elif position["type"] in ["buy_call", "sell_call", "buy_put", "sell_put"]:
                strike = position["strike_price"]
                premium = position["premium"]
                quantity = position["quantity"]
                if position["type"] == "buy_call":
                    total_pnl += quantity * (np.maximum(price_range - strike, 0) - premium)
                elif position["type"] == "sell_call":
                    total_pnl += quantity * (premium - np.maximum(price_range - strike, 0))
                elif position["type"] == "buy_put":
                    total_pnl += quantity * (np.maximum(strike - price_range, 0) - premium)
                elif position["type"] == "sell_put":
                    total_pnl += quantity * (premium - np.maximum(strike - price_range, 0))

        positive_mask = total_pnl > 0
        negative_mask = total_pnl <= 0

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=price_range[positive_mask],
            y=total_pnl[positive_mask],
            mode="lines",
            name="P&L (Positive)",
            line=dict(color="green")
        ))

        fig.add_trace(go.Scatter(
            x=price_range[negative_mask],
            y=total_pnl[negative_mask],
            mode="lines",
            name="P&L (Negative)",
            line=dict(color="red")
        ))

        fig.update_layout(
            title=f"P&L Graph for {symbol}",
            xaxis_title="Price",
            yaxis_title="P&L"
        )
        apply_dark_theme(fig)

        return fig
