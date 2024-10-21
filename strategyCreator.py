from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate

def create_strategy_creator_layout():
    return html.Div([
        html.H1("Strategy Creator"),
        html.Label("Strategy Name:"),
        dcc.Input(id="strategy-name", type="text", placeholder="Enter strategy name", style={'width': '100%'}),
        
        html.Label("Select Indicators:"),
        dcc.Dropdown(
            id="indicator-dropdown",
            options=[
                {'label': 'ROC', 'value': 'roc'},
                {'label': 'ATR', 'value': 'atr'},
                {'label': 'EMA', 'value': 'ema'}
            ],
            multi=True,
            placeholder="Select indicators",
            style={'width': '100%'},
            value=[]  # Start with no default value
        ),
        
        html.Div(id="dynamic-inputs"),  # Container for dynamic inputs
        
        html.Button("Create Strategy", id="create-strategy-btn", style={'margin-top': '10px', 'padding': '10px 20px', 'background-color': '#007BFF', 'color': 'white', 'border': 'none', 'border-radius': '5px', 'cursor': 'pointer'}),
        html.Div(id="strategy-feedback", style={'margin-top': '10px'})
    ])

def register_callbacks(app):
    @app.callback(
        Output("dynamic-inputs", "children"),
        Input("indicator-dropdown", "value")
    )
    def update_dynamic_inputs(selected_indicators):
        if not selected_indicators:
            return []

        inputs = []
        for indicator in selected_indicators:
            inputs.append(html.Div([
                html.Label(f"Length for {indicator}:"),
                dcc.Input(id=f"{indicator}-length", type="number", placeholder="Enter length", style={'width': '100%'}),
                html.Label(f"Logic for Buy Signal using {indicator}:"),
                dcc.Input(id=f"{indicator}-logic", type="text", placeholder="Enter logic (e.g., < threshold)", style={'width': '100%'})
            ], style={'margin-top': '10px'}))

        return inputs

    @app.callback(
        Output("strategy-feedback", "children"),
        Input("create-strategy-btn", "n_clicks"),
        State("strategy-name", "value"),
        State("indicator-dropdown", "value"),
    )
    def create_strategy(n_clicks, strategy_name, selected_indicators):
        if n_clicks is None:
            raise PreventUpdate

        if not strategy_name or not selected_indicators:
            return "Please fill in all fields."

        lengths = []
        buy_signal_logics = []
        
        for indicator in selected_indicators:
            length = dcc.Input(f"{indicator}-length")  # Fetch length
            logic = dcc.Input(f"{indicator}-logic")    # Fetch logic
            
            if length is None or logic is None:
                return f"Please define both length and logic for {indicator}."

            lengths.append(length)
            buy_signal_logics.append(logic)

        # Generate strategy code
        strategy_code = generate_strategy_code(strategy_name, selected_indicators, lengths, buy_signal_logics)

        # Write to dataManipulator.py
        with open('dataManipulator.py', 'a') as f:
            f.write(strategy_code)
        
        return f"Strategy '{strategy_name}' created successfully!"

def generate_strategy_code(strategy_name, indicators, lengths, buy_signal_logics):
    # Generate the strategy code based on the provided name, indicators, lengths, and buy signal logic
    indicator_definitions = ", ".join(indicators)
    
    code = f"""
# {strategy_name}

def create{strategy_name}Signals(df):
    add{strategy_name}Columns(df)
    create{strategy_name}BuySignals(df)
    remove{strategy_name}Columns(df)

def add{strategy_name}Columns(df):
"""
    
    for indicator, length in zip(indicators, lengths):
        code += f"    df['{indicator}'] = some_function(df['Close'], length={length})  # Update this line accordingly\n"
    
    code += f"""
    pass

def create{strategy_name}BuySignals(df):
    # Ensure the DataFrame has necessary columns
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date']  # Add required columns here
    assert all(col in df.columns for col in required_columns), \
        "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date' columns."
    
    # Create buy signal conditions
"""
    
    for indicator, logic in zip(indicators, buy_signal_logics):
        code += f"    buySignalCondition_{indicator} = (df['{indicator}'] {logic})\n"
    
    code += f"""
    # Combine all buy signals (example logic, adjust as needed)
    df['BUYSignal'] = buySignalCondition_roc | buySignalCondition_atr | buySignalCondition_ema  # Combine conditions
    pass

def remove{strategy_name}Columns(df):
    # Remove any temporary columns if needed
    pass
"""
    return code
