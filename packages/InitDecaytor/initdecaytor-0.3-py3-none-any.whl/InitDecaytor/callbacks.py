from dash import Input, Output, State, html
from InitDecaytor import time_factors
import InitDecaytor

def register_callbacks(app, app_instance):
    '''
    @app.callback(
        Output('output-container', 'children'),
        Input('submit-btn', 'n_clicks'),
        State('input-box', 'value')
    )
    def update_output(n_clicks, value):
        if n_clicks:
            app_instance._my_state = value  # safely update class state
            return f"You entered: {value}"
        return ""
    '''

    # Callback to update labels when Time unit changes
    @app.callback(
        Output("l-time_limit", "children"),
        Output("l-charge_time", "children"),
        Input("i-time_unit", "value"),
    )
    def change_time_unit(time_unit):
        # if hasattr(app_instance, 'simulation'):
        #     app_instance.simulation.set_time_unit(time_unit)
        return 'Time limit ({}):'.format(time_unit), 'Time ({}):'.format(time_unit)

    # Callback to update the settings
    @app.callback(
        Output("graph", "figure"),
        Input("b-update_settings", "n_clicks"),
        State("i-time_unit", "value"),
        State("i-time_limit", "value"),
        State("i-temperature", "value"),
        State("initiator_charges", "data"),
    )
    def update_settings(n, time_unit, time_limit, temperature, initiator_charges):
        app_instance.simulation = InitDecaytor.Simulation(temperature=temperature,
                                                          time_limit=time_limit,
                                                          time_unit=time_unit,
                                                          initiator_charges=initiator_charges if initiator_charges else None,
                                                          )
        fig = app_instance.simulation.plot_data(engine='plotly')
        return fig

    # Callback to append a new addition into the Store, update the list display, and the graph
    @app.callback(
        # Output("charges_list", "children"),
        Output("i-charges_list", "options"),
        Output("i-charges_list", "value"),
        Output("initiator_charges", "data"),
        # Output("graph", "figure"),
        Input("b-add_charge", "n_clicks"),
        State("i-charge_initiator", "value"),
        State("i-charge_time", "value"),
        State("i-charge_concentration", "value"),
        State("i-charges_list", "value"),
        State("initiator_charges", "data"),
        # allow_duplicate=True,
        prevent_initial_call=True,
    )
    def update_charges(n, initiator, time, charge, charges_list, initiator_charges):
        initiator_charges = [[initiator, time, charge] for i, [initiator, time, charge] in enumerate(initiator_charges) if i in charges_list]
        if n and charge:
            if [initiator, time, charge] not in initiator_charges:
                initiator_charges += [[initiator, time, charge]]
        # rebuild UL
        # charges_list = [html.Li(f"{charge[0]}: {charge[2]}wt% after {charge[1]}{app_instance.simulation.time_unit}") for charge in initiator_charges]
        # charges_list = [f'{charge[1]}{app_instance.simulation.time_unit}: {charge[2]}wt% {charge[0]}' for i, charge in enumerate(initiator_charges)]
        charges_list = [{'label': f'{charge[1]}{app_instance.simulation.time_unit}: {charge[2]}wt% {charge[0]}', 'value': i} for i, charge in enumerate(initiator_charges)]
        # Update simulation and graph
        app_instance.simulation.set_initiator_charges(initiator_charges)
        fig = app_instance.simulation.plot_data(engine='plotly')
        return charges_list, list(range(len(initiator_charges))), initiator_charges, #, fig

    '''
    # Callback to update the graph
    @app.callback(
        Output("graph", "figure"),
        Input("b-update_graph", "n_clicks"),
        State("initiator_charges", "data"),
        prevent_initial_call=True,
    )
    def update_graph(n, initiator_charges):
        fig = app_instance.simulation.plot_data(engine='plotly')
        return fig
    '''