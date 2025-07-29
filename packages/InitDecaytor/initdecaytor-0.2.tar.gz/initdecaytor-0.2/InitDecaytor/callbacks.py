from dash import Input, Output, State

def register_callbacks(app, app_instance):
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
