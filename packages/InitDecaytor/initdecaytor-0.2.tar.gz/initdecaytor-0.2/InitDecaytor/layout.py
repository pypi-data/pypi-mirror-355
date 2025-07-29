from dash import html, dcc
from InitDecaytor import hlt_parms, time_factors

time_unit = 'h'
time_factor = time_factors[time_unit]

def serve_layout():
    layout = html.Div([
        # html.H1("My Dash App"),
        # dcc.Input(id='input-box', type='text', value=''),
        # html.Button('Submit', id='submit-btn', n_clicks=0),
        # html.Div(id='output-container'),

        html.H2('Theoretical initiator decomposition'),

        html.H3('Setup'),
        html.Div([
            html.Label('Time unit:'),
            dcc.Dropdown(id="i-time_unit",
                         options=[{"label": unit, "value": unit} for unit in time_factors],
                         value=list(time_factors.keys())[2],
                         style={"width": "50px", 'height': '35px', 'minHeight': '35px', 'lineHeight': '35px', 'padding': '0 8px', 'fontSize': '14px', "display": "inline-block", "marginLeft": "5px"},
                         ),
        ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
        html.Div([
            html.Label('Time limit ({}):'.format(time_unit), id='l-time_limit'),
            dcc.Input(id="i-time_limit",
                      type="number",
                      value=20,
                      step=1,
                      style={"width": "80px", "marginLeft": "5px", "marginRight": "5px"},
                      ),
            dcc.Checklist(id='i-time_limit_auto',
                          options=[{"label": 'Auto time limit', "value": 'auto'}],
                          ),
        ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
        html.Div([
            html.Label("Temperature (°C):"),
            dcc.Input(id="i-temperature",
                      type="number",
                      value=60,
                      step=1,
                      style={"width": "80px", "marginLeft": "5px"},
                      ),
        ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
        html.Div([
            html.Button("Initialize",
                        id="b-initialize",
                        n_clicks=0,
                        style={},
                        ),
        ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),

        html.H3('Initiator charges'),
        html.Div([
            html.Label("Time (u)"),
            dcc.Input(id="add-time", type="number", value=0, step=0.1, style={"width": "80px"}),
            html.Label("Initiator", style={"marginLeft": "20px"}),
            dcc.Dropdown(id="add-initiator",
                         options=[{"label": ini, "value": ini} for ini in hlt_parms],
                         value=list(hlt_parms.keys())[0], style={"width": "150px", "display": "inline-block", "marginLeft": "5px"}),
            html.Label("Concentration (wt%)", style={"marginLeft": "20px"}),
            dcc.Input(id="add-conc", type="number", value=0.1, step=0.01, style={"width": "80px"}),
            html.Button("Voeg toe", id="add-button", n_clicks=0, style={"marginLeft": "20px"})
        ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),


        html.Div([
            html.H4("Huidige toevoegingen:"),
            html.Ul(id="add-list")
        ], style={"margin": "10px"}),

        # Store the list of additions
        dcc.Store(id="additions", data=[]),

        html.Hr(),

        html.Div([
            html.Label("Temperatuur (°C)"),
            dcc.Input(id="temp-input", type="number", value=80, step=1, style={"marginRight": "20px"}),

            html.Label("Simulatieduur (u)"),
            dcc.Input(id="time-input", type="number", value=20, step=1),
        ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),

        html.Button("Update grafiek", id="update-graph", n_clicks=0, style={"margin": "10px"}),
        dcc.Graph(id="concentration-graph")
    ])






    return layout
