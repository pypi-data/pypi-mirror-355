from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Qt

class Slider(QSlider):
    """A more intuitive slider widget."""

    def __init__(self, min_val: int = 0, max_val: int = 100, default_val: int = 0, on_change: callable = None, horizontal: bool = True, parent=None):
        orientation = Qt.Horizontal if horizontal else Qt.Vertical
        super().__init__(orientation, parent)
        
        self.setRange(min_val, max_val)
        self.setValue(default_val)
        
        if on_change:
            self.valueChanged.connect(on_change)
            
    def get_value(self) -> int:
        return self.value()
        
    def set_value(self, value: int):
        self.setValue(value) 