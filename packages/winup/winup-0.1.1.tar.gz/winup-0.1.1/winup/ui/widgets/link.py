from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import Qt

class Link(QLabel):
    def __init__(self, text: str, url: str, parent=None):
        super().__init__(text, parent)
        self.url = url
        self.setText(f'<a href="{url}">{text}</a>')
        self.setOpenExternalLinks(True)
        self.setStyleSheet("""
            QLabel {
                color: #007BFF;
                text-decoration: none;
            }
            QLabel:hover {
                text-decoration: underline;
            }
        """)

    def mousePressEvent(self, event):
        QDesktopServices.openUrl(self.url)
        super().mousePressEvent(event)
