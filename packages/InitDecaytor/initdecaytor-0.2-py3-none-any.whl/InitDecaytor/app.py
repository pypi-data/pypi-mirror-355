from dash import Dash
from .layout import serve_layout
from .callbacks import register_callbacks


class GUI:
    def __init__(self, name=__name__):
        self.app = Dash(name)
        self.app.layout = serve_layout()
        register_callbacks(self.app, self)  # pass self to access state in callbacks

    def run(self, **kwargs):
        self.app.run(**kwargs)




'''
    def get_state(self):
        return self._my_state

    def set_state(self, value):
        self._my_state = value
'''