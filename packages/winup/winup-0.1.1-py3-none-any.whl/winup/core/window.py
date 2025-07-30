# winup/core/window.py

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

class WinUpApp:
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self._main_window = None
        self._main_layout = None

    def create_window(self, title="WinUp App", width=640, height=480, icon=None):
        self._main_window = QMainWindow()
        self._main_window.setWindowTitle(title)
        self._main_window.resize(QSize(width, height))

        if icon:
            self._main_window.setWindowIcon(QIcon(icon))

        central_widget = QWidget()
        self._main_layout = QVBoxLayout()
        central_widget.setLayout(self._main_layout)
        self._main_window.setCentralWidget(central_widget)

    def add_widget(self, widget):
        if self._main_layout is None:
            raise RuntimeError("Window layout not initialized.")
        self._main_layout.addWidget(widget)

    def add_row(self, *widgets):
        layout = QHBoxLayout()
        for widget in widgets:
            layout.addWidget(widget)
        container = QWidget()
        container.setLayout(layout)
        self._main_layout.addWidget(container)
        return self

    def add_column(self, *widgets):
        layout = QVBoxLayout()
        for widget in widgets:
            layout.addWidget(widget)
        container = QWidget()
        container.setLayout(layout)
        self._main_layout.addWidget(container)
        return self

    def add_flex(self, direction: str = "row", widgets: list = []):
        if direction == "row":
            layout = QHBoxLayout()
        elif direction == "column":
            layout = QVBoxLayout()
        else:
            raise ValueError("direction must be 'row' or 'column'")

        for widget in widgets:
            layout.addWidget(widget)

        container = QWidget()
        container.setLayout(layout)
        self._main_layout.addWidget(container)
        return self

    def add_grid(self, cells: list[list]):
        layout = QGridLayout()

        for row_index, row in enumerate(cells):
            for col_index, widget in enumerate(row):
                if widget:  # skip None values
                    layout.addWidget(widget, row_index, col_index)

        container = QWidget()
        container.setLayout(layout)
        self._main_layout.addWidget(container)
        return self

    def show(self):
        if not self._main_window:
            raise RuntimeError("No window to show.")
        self._main_window.show()
        return self.app.exec()

# Singleton instance
_winup_app = WinUpApp()
