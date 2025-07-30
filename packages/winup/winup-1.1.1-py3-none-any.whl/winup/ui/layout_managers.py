from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import Qt

class VBox(QVBoxLayout):
    """A low-level vertical layout manager."""
    def __init__(self, parent: QWidget = None, props: dict = None):
        super().__init__(parent)
        if props:
            self._apply_props(props)

    def _apply_props(self, props: dict):
        alignment = props.get("alignment")
        spacing = props.get("spacing")
        margin = props.get("margin")

        if alignment and hasattr(Qt.AlignmentFlag, alignment):
            self.setAlignment(getattr(Qt.AlignmentFlag, alignment))
        if spacing is not None:
            self.setSpacing(spacing)
        if margin is not None:
            if isinstance(margin, int):
                self.setContentsMargins(margin, margin, margin, margin)
            elif isinstance(margin, (list, tuple)) and len(margin) == 4:
                self.setContentsMargins(*margin)

class HBox(QHBoxLayout):
    """A low-level horizontal layout manager."""
    def __init__(self, parent: QWidget = None, props: dict = None):
        super().__init__(parent)
        if props:
            self._apply_props(props)

    def _apply_props(self, props: dict):
        alignment = props.get("alignment")
        spacing = props.get("spacing")
        margin = props.get("margin")

        if alignment and hasattr(Qt.AlignmentFlag, alignment):
            self.setAlignment(getattr(Qt.AlignmentFlag, alignment))
        if spacing is not None:
            self.setSpacing(spacing)
        if margin is not None:
            if isinstance(margin, int):
                self.setContentsMargins(margin, margin, margin, margin)
            elif isinstance(margin, (list, tuple)) and len(margin) == 4:
                self.setContentsMargins(*margin)
