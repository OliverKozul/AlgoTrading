from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash.dependencies import ALL
import json
import strategies.strategy_tester as st

def create_strategy_creator_tab_layout():
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
            value=[]
        ),
        
        html.Div(id="dynamic-inputs"),  # Container for dynamic inputs
        
        html.Button("Create Strategy", id="create-strategy-btn", style={
            'margin-top': '10px', 
            'padding': '10px 20px', 
            'background-color': '#007BFF', 
            'color': 'white', 
            'border': 'none', 
            'border-radius': '5px', 
            'cursor': 'pointer'}),
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
                dcc.Input(id={"type": "indicator-length", "indicator": indicator}, type="number", placeholder="Enter length", style={'width': '100%'}),
                html.Label(f"Logic for Buy Signal using {indicator}:"),
                dcc.Input(id={"type": "indicator-logic", "indicator": indicator}, type="text", placeholder="Enter logic (e.g., < threshold)", style={'width': '100%'})
            ], style={'margin-top': '10px'}))

        return inputs

    @app.callback(
        Output("strategy-feedback", "children"),
        Input("create-strategy-btn", "n_clicks"),
        State("strategy-name", "value"),
        State("indicator-dropdown", "value"),
        State({"type": "indicator-length", "indicator": ALL}, "value"),  # Fetch all indicator lengths
        State({"type": "indicator-logic", "indicator": ALL}, "value")    # Fetch all indicator logics
    )
    def create_strategy(n_clicks, strategy_name, selected_indicators, lengths, logics):
        if n_clicks is None:
            raise PreventUpdate

        if not strategy_name or not selected_indicators or not lengths or not logics:
            return "Please fill in all fields."
        
        if strategy_name.isalpha() == False:
            return "Strategy name can only be comprised of letters."

        # Generate strategy code
        strategy_code = generate_strategy_code(strategy_name, selected_indicators, lengths, logics)

        # Write to data_manipulator.py
        with open('core\data_manipulator.py', 'a') as f:
            f.write(strategy_code)

        strategies = st.load_strategies_from_json('strategies\community_strategies.json')

        # Add the new strategy (strat3)
        strategies[strategy_name] = 0

        # Write the updated JSON back to the file
        with open('strategies\community_strategies.json', 'w') as f:
            json.dump(strategies, f, indent=4)

        classCode = generate_class_code(strategy_name)

        with open('strategies\strats.py', 'a') as f:
            f.write(classCode)

        return f"Strategy '{strategy_name}' created successfully!"

def generate_strategy_code(strategy_name, indicators, lengths, logics):
    code = f"""
    
# {strategy_name}

def create{strategy_name[0].upper()}{strategy_name[1:]}Signals(df):
    add{strategy_name}Columns(df)
    create{strategy_name}BuySignals(df)
    remove{strategy_name}Columns(df)

def add{strategy_name}Columns(df):
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
"""
    for indicator, length in zip(indicators, lengths):
        if indicator == 'atr':
            code += f"    df['{indicator}'] = ta.{indicator}(df['High'], df['Low'], df['Close'], length={length})\n"
        else:
            code += f"    df['{indicator}'] = ta.{indicator}(df['Close'], length={length})\n"
    code += "    df.dropna(inplace=True)\n"
    code += f"""
def create{strategy_name}BuySignals(df):
    required_columns = ['Open', 'High', 'Low', 'Close', 'Date']
    assert all(col in df.columns for col in required_columns), "DataFrame must contain 'Open', 'High', 'Low', 'Close', 'Date' columns."

"""
    for indicator, logic in zip(indicators, logics):
        code += f"    buySignalCondition_{indicator} = (df['{indicator}'] {logic})\n"
        code += f"    df['BUYSignal'] = df['BUYSignal'] | buySignalCondition_{indicator}\n"
    
    code += f"""
def remove{strategy_name}Columns(df):"""
    for indicator in indicators:
        code += f"""
    df.drop(columns=['{indicator}'], inplace=True)"""

    return code

def generate_class_code(strategy_name):
    code = f"""
class {strategy_name}(BaseStrategy):
    def init(self):
        super().init()
        self.atrCoef = 6

    def next(self):
        super().next()
"""
    
    return code
    