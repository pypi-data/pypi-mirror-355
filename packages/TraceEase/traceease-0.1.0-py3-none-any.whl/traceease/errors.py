from .utils import load_path

class Error:
    def __init__(self, type):
        self.type = type
        self.errors = load_path('errors.json')
        self.unhandled_message = f"We don't currently have support for this error! \nWe'd love your feedback however. \nFeel free to report this oversight to our GitHub repo."

    def __str__(self):
        return f'{self.errors.get(self.type, self.unhandled_message)}' 