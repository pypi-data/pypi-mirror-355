# winup/ui/input.py
import re
from typing import Union, Callable
from PySide6.QtWidgets import QLineEdit
from ... import style
from ...state import state as global_state

# Pre-compiled regex for common validation types
VALIDATION_PATTERNS = {
    "email": re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"),
    "integer": re.compile(r"^-?\d+$"),
    "decimal": re.compile(r"^-?\d+(\.\d+)?$"),
}

class Input(QLineEdit):
    def __init__(self, placeholder="", text="", props=None, validation=None, **kwargs):
        super().__init__(**kwargs)
        if placeholder:
            self.setPlaceholderText(placeholder)
        if text:
            self.setText(text)
            
        self.validation_rule = validation
        self.textChanged.connect(self._on_text_changed)
        
        if props:
            style.styler.apply_props(self, props)
        
        # Initial validation check
        self._on_text_changed(self.text())

    def _validate(self, text: str):
        """Internal method to check text against the validation rule."""
        is_valid = False
        if isinstance(self.validation_rule, re.Pattern):
            is_valid = bool(self.validation_rule.match(text))
        elif callable(self.validation_rule):
            is_valid = self.validation_rule(text)
        
        # Use the styler to toggle classes
        style.styler.toggle_class(self, "valid", is_valid)
        style.styler.toggle_class(self, "invalid", not is_valid)

    def _on_text_changed(self, text: str):
        self._validate(text)

    def set_text(self, text: str):
        """A more Pythonic alias for setText()."""
        self.setText(text)
        
    def get_text(self) -> str:
        """A more Pythonic alias for text()."""
        return self.text()