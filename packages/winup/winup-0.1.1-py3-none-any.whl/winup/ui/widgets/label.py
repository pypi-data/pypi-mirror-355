from PySide6.QtWidgets import QLabel
from ... import style

class Label(QLabel):
    def __init__(self, text="", props=None, **kwargs):
        super().__init__(text, **kwargs)
        if props:
            style.styler.apply_props(self, props)

    def set_text(self, text: str):
        """A more Pythonic alias for setText()."""
        self.setText(text)
