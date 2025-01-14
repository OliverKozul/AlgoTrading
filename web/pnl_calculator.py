from dash import dcc, html, Input, Output, State, callback, ctx, ALL
from dash.exceptions import PreventUpdate
import core.data_manipulator as dm
import numpy as np
import plotly.graph_objects as go

symbols = dm.load_symbols('SP')

def create_pnl_calculator_tab_layout():
    return html.Div([
        html.H1("P&L Calculator"),

        # Symbol Selection
        html.Label("Select Symbol:"),
        dcc.Dropdown(
            id="symbol-dropdown",
            options=symbols,
            value="AAPL",
            placeholder="Select a symbol",
            style={'width': '100%'}
        ),

        # Add Position
        html.Label("Position Type:"),
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
            style={'width': '100%'}
        ),

        html.Div(id="position-inputs"),

        html.Button("Add Position", id="add-position-btn", style={
            'margin-top': '10px',
            'padding': '10px 20px',
            'background-color': '#007BFF',
            'color': 'white',
            'border': 'none',
            'border-radius': '5px',
            'cursor': 'pointer'
        }),

        # Positions List
        html.Hr(),
        html.Div(id="positions-list", style={'margin-top': '20px'}),

        # P&L Graph
        html.Hr(),
        dcc.Graph(id="pnl-graph"),
        dcc.Store(id="positions-data", data=[])  # Store positions
    ])

def register_callbacks(app):
    # Callback for updating position input fields based on selected position type
    @app.callback(
        Output("position-inputs", "children"),
        Input("position-type", "value"),
    )
    def update_position_inputs(position_type):
        # Default disabled states for inputs based on position type
        disabled_states = {
            "stock": {"buy-price": False, "strike-price": True, "premium": True, "position-quantity": False},
            "buy_call": {"buy-price": True, "strike-price": False, "premium": False, "position-quantity": False},
            "buy_put": {"buy-price": True, "strike-price": False, "premium": False, "position-quantity": False},
            "sell_call": {"buy-price": True, "strike-price": False, "premium": False, "position-quantity": False},
            "sell_put": {"buy-price": True, "strike-price": False, "premium": False, "position-quantity": False},
        }

        # Determine current disabled state or default to all disabled if no type is selected
        state = disabled_states.get(position_type, {"buy-price": True, "strike-price": True, "premium": True, "position-quantity": True})

        # Render all input fields, graying out irrelevant ones
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


    # Unified callback for adding and removing positions
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
    def modify_positions(add_click, remove_clicks, positions, position_type, buy_price, strike_price, premium, quantity):
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

            # Add new position
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

        # Render positions list
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

    # Callback for updating P&L graph
    @app.callback(
        Output("pnl-graph", "figure"),
        Input("positions-data", "data"),
        Input("symbol-dropdown", "value"),
    )
    def update_pnl_graph(positions, symbol):
        if not positions:
            return go.Figure()

        # Calculate the price range dynamically
        min_price_in_positions = min(
            [pos["buy_price"] if pos["type"] == "stock" else pos["strike_price"] for pos in positions]
        )
        max_price_in_positions = max(
            [pos["buy_price"] if pos["type"] == "stock" else pos["strike_price"] for pos in positions]
        )
        price_range = np.linspace(0.9 * min_price_in_positions, 1.1 * max_price_in_positions, 500)

        # Initialize total P&L
        total_pnl = np.zeros_like(price_range)

        # Calculate P&L for each position
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

        # Split the total_pnl into positive and negative components
        positive_mask = total_pnl > 0
        negative_mask = total_pnl <= 0

        fig = go.Figure()

        # Add positive P&L line (green)
        fig.add_trace(go.Scatter(
            x=price_range[positive_mask],
            y=total_pnl[positive_mask],
            mode="lines",
            name="P&L (Positive)",
            line=dict(color="green")
        ))

        # Add negative P&L line (red)
        fig.add_trace(go.Scatter(
            x=price_range[negative_mask],
            y=total_pnl[negative_mask],
            mode="lines",
            name="P&L (Negative)",
            line=dict(color="red")
        ))

        # Update layout
        fig.update_layout(
            title=f"P&L Graph for {symbol}",
            xaxis_title="Price",
            yaxis_title="P&L",
            template="plotly_white"
        )

        return fig

