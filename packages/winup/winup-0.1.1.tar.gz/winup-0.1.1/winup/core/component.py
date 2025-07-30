import functools
from PySide6.QtWidgets import QWidget, QVBoxLayout

def component(func):
    """
    A decorator that turns a function into a WinUp component.

    The decorated function should return a QWidget or a list of QWidgets.
    These widgets will be automatically placed in a container with a
    vertical layout.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a container widget that will represent the component
        container = QWidget()
        # Use a vertical layout by default for the component's children
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0) # Remove padding
        container.setLayout(layout)

        # Call the user's function to get the widget(s)
        result = func(*args, **kwargs)

        # Add the returned widget(s) to the component's layout
        if isinstance(result, list):
            for widget in result:
                layout.addWidget(widget)
        elif isinstance(result, QWidget):
            layout.addWidget(result)
        else:
            raise TypeError(
                f"Component '{func.__name__}' must return a QWidget or a list of QWidgets, "
                f"but it returned type '{type(result).__name__}'."
            )

        return container

    return wrapper 