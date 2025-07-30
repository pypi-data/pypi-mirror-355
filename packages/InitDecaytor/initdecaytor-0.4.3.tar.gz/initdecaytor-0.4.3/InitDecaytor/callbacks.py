from dash import Input, Output, State, html
from InitDecaytor import time_factors, source_encoding
import InitDecaytor
import io, base64

def register_callbacks(app, app_instance):

    # This simulates an "on load" by updating Store when app loads
    @app.callback(
        Output('initialization', 'data'),
        Input('initialization', 'data'),
        prevent_initial_call=False  # run on load
    )
    def initialize_data(data):
        app_instance.delete_temperature_profile()
        return {'initialized': True}

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

    # Callback to enable/disable the trim_data checkbox in order to avoid impossible input
    @app.callback(
        Output("i-trim_data", "value"),
        Output("i-trim_data", "options"),
        Input("i-time_limit", "value"),
        State("i-trim_data", "value"),
        State("i-trim_data", "options"),
        prevent_initial_call=True,
    )
    def disable_trim_data(time_limit, trim_data, trim_data_options):
        trim_data_options[0]['disabled'] = True if not time_limit else False
        return ['trim_data'] if not time_limit else trim_data, trim_data_options

    # Callback to enable/disable the trim_threshold field
    @app.callback(
        Output("i-trim_threshold", "disabled"),
        Input("i-trim_data", "value"),
        prevent_initial_call=True,
    )
    def disable_threshold(trim_data):
        return True if not trim_data else False

    # This disables the unit field as soon as charges are added to prevent unit mixups
    @app.callback(
        Output("i-initiator_charges_unit", "disabled"),
        Input('initiator_charges', 'data'),
        prevent_initial_call=True,
    )
    def disable_initiator_charges_unit(data):
        return True

    # Callback to update the settings and graph
    @app.callback(
        Output("graph", "figure"),
        Input("b-update_graph", "n_clicks"),
        State("i-time_unit", "value"),
        State("i-time_limit", "value"),
        State("i-trim_data", "value"),
        State("i-trim_threshold", "value"),
        State("i-plot_relative_concentration", "value"),
        State("i-temperature", "value"),
        State("initiator_charges", "data"),
        State("i-initiator_charges_unit", "value"),
    )
    def update_graph(n, time_unit, time_limit, trim_data, trim_threshold, plot_relative_concentration, temperature, initiator_charges, initiator_charges_unit):
        if hasattr(app_instance, 'temperature_profile'):
            app_instance.simulation = InitDecaytor.Simulation(temperature=app_instance.temperature_profile,
                                                              time_limit=time_limit,
                                                              time_unit=time_unit,
                                                              initiator_charges=initiator_charges if initiator_charges else None,
                                                              initiator_charges_unit=initiator_charges_unit,
                                                              trim_data=True if trim_data else False,
                                                              trim_threshold=trim_threshold / 100 if trim_threshold else 1e-4,
                                                              )
        else:
            app_instance.simulation = InitDecaytor.Simulation(temperature=temperature,
                                                              time_limit=time_limit,
                                                              time_unit=time_unit,
                                                              initiator_charges=initiator_charges if initiator_charges else None,
                                                              initiator_charges_unit=initiator_charges_unit,
                                                              trim_data=True if trim_data else False,
                                                              trim_threshold=trim_threshold / 100 if trim_threshold else 1e-4,
                                                              )
        fig = app_instance.simulation.plot_data(plot_relative_concentration=True if plot_relative_concentration else False,
                                                engine='plotly')
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
        State("i-initiator_charges_unit", "value"),
        # allow_duplicate=True,
        prevent_initial_call=True,
    )
    def update_charges(n, initiator, time, charge, charges_list, initiator_charges, initiator_charges_unit):
        initiator_charges = [[initiator, time, charge] for i, [initiator, time, charge] in enumerate(initiator_charges) if i in charges_list]
        if n and charge:
            if [initiator, time, charge] not in initiator_charges:
                initiator_charges += [[initiator, time, charge]]
        # rebuild UL
        # charges_list = [html.Li(f"{charge[0]}: {charge[2]}wt% after {charge[1]}{app_instance.simulation.time_unit}") for charge in initiator_charges]
        # charges_list = [f'{charge[1]}{app_instance.simulation.time_unit}: {charge[2]}wt% {charge[0]}' for i, charge in enumerate(initiator_charges)]
        charges_list = [{'label': f'{charge[1]}{app_instance.simulation.time_unit}: {charge[2]}{initiator_charges_unit} {charge[0]}', 'value': i} for i, charge in enumerate(initiator_charges)]
        # Update simulation and graph
        app_instance.simulation.set_initiator_charges(initiator_charges)
        fig = app_instance.simulation.plot_data(engine='plotly')
        return charges_list, list(range(len(initiator_charges))), initiator_charges, #, fig

    # Load and process temperature profile
    @app.callback(
        Output('l-temperature_profile', 'children'),
        Output("i-temperature", "disabled"),
        Input('i-temperature_profile', 'contents'),
        State('i-temperature_profile', 'filename'),
        State('i-source', 'value'),
        prevent_initial_call=True,
    )
    def update_temperature_profile(contents, filename, source):
        if contents is not None:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            try:
                file_like = io.StringIO(decoded.decode(source_encoding[source]))
                app_instance.read_temperature_profile(filename, file_like, source)
                return 'Profile: {}'.format(filename), True
            except:
                return 'Profile: Failed to load {}'.format(filename), False
        else:
            return 'Profile:', False

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