from PySide6.QtWidgets import QFrame, QWidget
from ..layout_managers import VBox
from ... import style

class Frame(QFrame):
    def __init__(self, children: list = None, props: dict = None, **kwargs):
        super().__init__(**kwargs)
        self._layout = None
        
        if props:
            style.styler.apply_props(self, props)
        
        # If children are provided, we must set a layout for them.
        # We'll use a VBox by default.
        if children:
            self.set_layout(VBox())
            for child in children:
                self.add_child(child)

    def set_layout(self, layout):
        # Clear any existing layout and its widgets before setting a new one.
        if self.layout():
            while self.layout().count():
                item = self.layout().takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        self.setLayout(layout)
        self._layout = layout

    def add_child(self, child: QWidget):
        # If no layout exists, create a default one to hold the new child.
        if not self._layout:
            self.set_layout(VBox())
        
        if hasattr(self._layout, 'addWidget'):
            self._layout.addWidget(child)
        else:
            raise TypeError("The layout for this Frame does not support adding widgets.")