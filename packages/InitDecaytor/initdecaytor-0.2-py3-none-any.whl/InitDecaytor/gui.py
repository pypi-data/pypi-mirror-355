# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 Kevin De Bruycker and Stijn D'hollander
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import numpy as np
import pandas as pd
from scipy.optimize import fsolve
# from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from numba import njit
import dash
from dash import dcc, html, Input, Output, State
from spycontrol import import_spycontrol_data
# import plotly.io as pio
# pio.renderers.default = 'browser'

from InitDecaytor import hlt_parms, time_factors, Simulation

time_unit = 'h'
time_factor = time_factors[time_unit]

def GUI():
    app = dash.Dash(__name__)
    server = app.server

    initiators = list(hlt_parms.keys())

    app.layout = html.Div([
        html.H2("Theoretical initiator decomposition"),

        html.H3('Setup'),
        html.Div([
            html.Label("Time unit:"),
            dcc.Dropdown(id="d-time_unit",
                         options=[{"label": unit, "value": unit} for unit in time_factors],
                         value=list(time_factors.keys())[2],
                         style={"width": "50px", "display": "inline-block", "marginLeft": "5px"},
                         ),
        ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
        html.Div([
            html.Label('Time limit ({}):'.format(time_unit), id='l-time_limit'),
            dcc.Input(id="d-time_limit",
                      type="number",
                      value=20,
                      step=1,
                      style={"width": "80px", "marginLeft": "5px", "marginRight": "5px"}
                      ),
            dcc.Checklist(id='d-time_limit_auto',
                          options=[{"label": 'Auto time limit', "value": 'auto'}],
                          ),
        ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),
        html.Div([
            html.Br(),
            html.Label("Temperature (°C):"),
            dcc.Input(id="d-temperature",
                      type="number",
                      value=60,
                      step=1,
                      style={"width": "80px", "marginLeft": "5px"}
                      ),
        ], style={"margin": "10px", "display": "flex", "alignItems": "center"}),

        html.H3('Initiator charges'),

        html.Div([
            html.Label("Time (u)"),
            dcc.Input(id="add-time", type="number", value=0, step=0.1, style={"width": "80px"}),
            html.Label("Initiator", style={"marginLeft": "20px"}),
            dcc.Dropdown(id="add-initiator",
                         options=[{"label": ini, "value": ini} for ini in initiators],
                         value=initiators[0], style={"width": "150px", "display": "inline-block", "marginLeft": "5px"}),
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

    # Callback to update labels when Time unit changes
    @app.callback(
        Output("l-time_limit", "children"),
        Input("d-time_unit", "value"),
    )
    def change_time_unit(value):
        global time_unit
        time_unit = value
        global time_factor
        time_factor = time_factors[value]
        return 'Time limit ({}):'.format(value)

    # Callback to append a new addition into the Store and update list display
    @app.callback(
        Output("additions", "data"),
        Output("add-list", "children"),
        Output("add-time", "value"),
        Output("add-initiator", "value"),
        Output("add-conc", "value"),
        Input("add-button", "n_clicks"),
        State("add-time", "value"),
        State("add-initiator", "value"),
        State("add-conc", "value"),
        State("additions", "data"),
    )
    def add_entry(n, t, ini, conc, stored):
        if n and t is not None and ini and conc is not None:
            new = {"time": float(t), "initiator": ini, "conc": float(conc)}
            stored = stored + [new]
        # rebuild UL
        items = [html.Li(f"{e['time']} u – {e['initiator']} : {e['conc']} wt%") for e in stored]
        # reset inputs
        return stored, items, 0, initiators[0], 0

    # Callback to generate the concentration graph from all additions
    @app.callback(
        Output("concentration-graph", "figure"),
        Input("update-graph", "n_clicks"),
        State("additions", "data"),
        State("temp-input", "value"),
        State("time-input", "value"),
    )
    def update_graph(n, additions, temp_C, duration_hr):
        temp_K = temp_C + 273.15
        # time vector in seconds
        t = np.arange(0, duration_hr * 3600, dtype="float64")
        dt = np.diff(t, prepend=0)
        df = pd.DataFrame({"time": t, "temperature": temp_K})

        # group additions by initiator
        events = {}
        for e in additions:
            sec = e["time"] * 3600
            events.setdefault(e["initiator"], []).append((sec, e["conc"]))

        # simulate each initiator
        for ini, fn in hlt_parms.items():
            if ini in events:
                c = np.zeros_like(t)
                for i in range(1, len(t)):
                    hl = fn(temp_K)
                    c[i] = c[i - 1] * np.exp(-dt[i] * np.log(2) / hl)
                    # check all events for this ini
                    for t_ev, amt in events[ini]:
                        if t[i - 1] < t_ev <= t[i]:
                            c[i] += amt
                df[ini] = c

        # build figure
        fig = go.Figure()
        for ini in events:
            fig.add_trace(go.Scatter(
                x=df["time"] / 3600, y=df[ini],
                mode="lines", name=ini,
                hovertemplate="%{y:.4f} wt% bij %{x:.2f} u"
            ))

        # temperature on secondary axis
        fig.add_trace(go.Scatter(
            x=df["time"] / 3600, y=df["temperature"] - 273.15,
            name="Temperatuur (°C)",
            line=dict(dash="dot", color="gray"), yaxis="y2"
        ))

        fig.update_layout(
            xaxis_title="Tijd (uren)",
            yaxis=dict(title="Initiatorconcentratie (wt%)"),
            yaxis2=dict(title="Temperatuur (°C)", overlaying="y", side="right"),
            legend=dict(x=0.7, y=1.1)
        )
        return fig

    if __name__ == "__main__":
        app.run(debug=True)

    app.run(debug=True)
