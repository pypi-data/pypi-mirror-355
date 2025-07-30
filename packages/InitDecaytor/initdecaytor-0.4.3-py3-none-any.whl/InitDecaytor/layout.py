from dash import html, dcc
from InitDecaytor import hlt_parms, time_factors, supported_sources

time_unit = 'h'
time_factor = time_factors[time_unit]

def serve_layout():
    layout = html.Div([
        dcc.Store(id='initialization'),

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
                    dcc.Checklist(id='i-trim_data',
                                  options=[{'label': 'Trim time (rel. initiator threshold of ', 'value': 'trim_data', 'disabled': False}],
                                  value=['trim_data'],
                                  ),
                    dcc.Input(id="i-trim_threshold",
                              type="number",
                              value=0.01,
                              step=0.01,
                              style={"width": "40px", "marginLeft": "5px"},
                              ),
                    html.Label('%)'),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                html.Div([
                    dcc.Checklist(id='i-plot_relative_concentration',
                                  options=[{'label': 'Plot relative concentrations', 'value': 'plot_relative_concentration'}],
                                  value=['plot_relative_concentration'],
                                  ),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                html.H4('Temperature (°C)'),
                html.Div([
                    html.Label("Profile:", id='l-temperature_profile'),
                    dcc.Dropdown(id="i-source",
                                 options=[{"label": source, "value": supported_sources[source]} for source in
                                          supported_sources],
                                 value=supported_sources[list(supported_sources.keys())[0]],

                                 style={"width": "150px", "display": "inline-block", "marginLeft": "5px"},
                                 ),
                    dcc.Upload(id='i-temperature_profile',
                               children=html.Button('Browse CSV'),
                               multiple=False,
                               accept='.csv',
                               style={"marginLeft": "10px"},
                               ),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Label("or fixed value:"),
                    dcc.Input(id="i-temperature",
                              type="number",
                              value=60,
                              step=1,
                              style={"width": "80px", "marginLeft": "5px"},
                              ),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
            ], style={"flex": "1", "padding": "10px"}),

            html.Div([
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
                        html.Label("Concentration:"),
                        dcc.Input(id="i-charge_concentration",
                                  type="number",
                                  value=0.1,
                                  # step=0.01,
                                  style={"width": "80px", "marginLeft": "5px"}),
                        dcc.Input(id="i-initiator_charges_unit",
                                  type="text",
                                  value='wt%',
                                  style={"width": "40px"}),
                    ],  style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                    html.Div([
                        html.Button("Add initiator charge",
                                    id="b-add_charge",
                                    n_clicks=0,
                                    style={"padding": "5px 10px", },
                                    ),
                    ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                ], ),

                html.Div([
                    html.Div([
                        html.Button("Update graph",
                                    id="b-update_graph",
                                    n_clicks=0,
                                    style={"padding": "10px 20px",
                                           "fontWeight": "bold",
                                           "backgroundColor": "#007BFF",
                                           "color": "white",
                                           "border": "none",
                                           "borderRadius": "6px",
                                           "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
                                           "fontSize": "16px",
                                           "cursor": "pointer",
                                           "transition": "0.3s",
                                           },
                                    ),
                    ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
                ],),
            ], style={"flex": "1", "padding": "10px", "display": "flex", "flexDirection": "column", "justifyContent": "space-between"}),

            html.Div([
                html.H3("List of initiator charges"),
                html.Div([
                    dcc.Checklist(id='i-charges_list',
                                  options=[],
                                  value=[],
                                  ),
                ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
            ], style={"flex": "1", "padding": "10px"}),
        ], style={"display": "flex", "flexWrap": "wrap", "gap": "20px", "alignItems": "top"}),

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