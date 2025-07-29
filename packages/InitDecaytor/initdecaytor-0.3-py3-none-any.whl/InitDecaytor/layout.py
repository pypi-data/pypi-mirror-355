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

        html.Div([
            html.Div([
                html.H3('Setup'),
                html.Div([
                    html.Label('Time unit:'),
                    dcc.Dropdown(id="i-time_unit",
                                 options=[{"label": unit, "value": unit} for unit in time_factors],
                                 value=list(time_factors.keys())[2],
                                 style={"width": "50px", "display": "inline-block", "marginLeft": "5px"},
                                 ),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Label('Time limit ({}):'.format(time_unit), id='l-time_limit'),
                    dcc.Input(id="i-time_limit",
                              type="number",
                              value=20,
                              step=1,
                              style={"width": "80px", "marginLeft": "5px"},
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
                    html.Button("Update graph",
                                id="b-update_settings",
                                n_clicks=0,
                                style={"padding": "5px 10px", },
                                ),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
            ], style={"flex": "1", "padding": "10px"}),

            html.Div([
                html.H3('Initiator charges'),
                html.Div([
                    html.Label("Initiator:"),
                    dcc.Dropdown(id="i-charge_initiator",
                                 options=[{"label": ini, "value": ini} for ini in hlt_parms],
                                 value=list(hlt_parms.keys())[0],
                                 style={"width": "150px", "display": "inline-block", "marginLeft": "5px"}
                                 ),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Label('Time ({}):'.format(time_unit), id='l-charge_time'),
                    dcc.Input(id="i-charge_time",
                              type="number",
                              value=0,
                              step=0.1,
                              style={"width": "80px", "marginLeft": "5px"},
                              ),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Label("Concentration (wt%):"),
                    dcc.Input(id="i-charge_concentration",
                              type="number",
                              value=0.1,
                              step=0.01,
                              style={"width": "80px", "marginLeft": "5px"}),
                ],  style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Button("Add initiator charge",
                                id="b-add_charge",
                                n_clicks=0,
                                style={"padding": "5px 10px", },
                                ),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
            ], style={"flex": "3", "padding": "10px"}),
        ], style={"display": "flex", "gap": "20px"}),

        html.Hr(),

        html.Div([
            html.H3("List of initiator charges:"),
            # html.Ul(id="charges_list"),
            dcc.Checklist(id='i-charges_list',
                          options=[],
                          value=[],
                          ),
        ], style={"margin": "10px"}),

        # Store the list of additions
        dcc.Store(id="initiator_charges", data=[]),

        html.Hr(),

        dcc.Graph(id="graph")
    ])






    return layout

'''
        html.Div([
            html.Button("Update graph",
                        id="b-update_graph",
                        n_clicks=0,
                        style={"padding": "5px 10px", },
                        ),
        ], style={"margin": "20px", "display": "flex", "alignItems": "center"}),

'''