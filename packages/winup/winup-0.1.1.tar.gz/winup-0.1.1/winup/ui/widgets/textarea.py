# winup/ui/textarea.py
from PySide6.QtWidgets import QTextEdit

class Textarea(QTextEdit):
    def __init__(self, placeholder: str = "", text: str = "", parent=None):
        super().__init__(parent)
        if text:
            self.setPlainText(text)
        if placeholder:
            self.setPlaceholderText(placeholder)
