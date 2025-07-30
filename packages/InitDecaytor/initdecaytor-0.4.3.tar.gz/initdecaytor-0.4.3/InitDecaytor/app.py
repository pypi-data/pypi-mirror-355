from dash import Dash
from .layout import serve_layout
from .callbacks import register_callbacks
from InitDecaytor import get_temperature_profile

class GUI:
    def __init__(self, name=__name__):
        self.app = Dash(name)
        self.app.layout = serve_layout()
        register_callbacks(self.app, self)  # pass self to access state in callbacks

    def run(self, **kwargs):
        self.app.run(**kwargs)

    def read_temperature_profile(self, filename, file_like, source):
        self.filename = filename
        self.temperature_profile = get_temperature_profile(StringIO=file_like, source=source)

    def delete_temperature_profile(self):
        if hasattr(self, 'filename'):
            del self.filename
            del self.temperature_profile


'''
    def get_state(self):
        return self._my_state

    def set_state(self, value):
        self._my_state = value
'''