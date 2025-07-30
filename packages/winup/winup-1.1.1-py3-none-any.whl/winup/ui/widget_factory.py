"""
Centralized factory and registry for all UI widgets in WinUp.
This allows developers to override default widgets with their own custom implementations.
"""

# Default widget implementations
from .widgets.button import Button as DefaultButton
from .widgets.calendar import Calendar as DefaultCalendar
from .widgets.deck import Deck as DefaultDeck
from .widgets.frame import Frame as DefaultFrame
from .widgets.image import Image as DefaultImage
from .widgets.input import Input as DefaultInput
from .widgets.label import Label as DefaultLabel
from .widgets.link import Link as DefaultLink
from .widgets.progress_bar import ProgressBar as DefaultProgressBar
from .widgets.slider import Slider as DefaultSlider
from .widgets.textarea import Textarea as DefaultTextarea
from .layouts import Column as DefaultColumn, Row as DefaultRow

# The central registry for widget classes
_WIDGET_REGISTRY = {
    "Button": DefaultButton,
    "Calendar": DefaultCalendar,
    "Deck": DefaultDeck,
    "Frame": DefaultFrame,
    "Image": DefaultImage,
    "Input": DefaultInput,
    "Label": DefaultLabel,
    "Link": DefaultLink,
    "ProgressBar": DefaultProgressBar,
    "Slider": DefaultSlider,
    "Textarea": DefaultTextarea,
    "Column": DefaultColumn,
    "Row": DefaultRow,
}

def register_widget(name: str, widget_class: type):
    """
    Registers a custom widget class to be used by the framework.
    This will override the default widget with the same name.

    Args:
        name: The name of the widget to override (e.g., "Button").
        widget_class: The new class to be used for this widget.
    """
    _WIDGET_REGISTRY[name] = widget_class
    print(f"Custom widget '{name}' registered.")

def create_widget(name: str, *args, **kwargs):
    """
    Creates an instance of a widget from the registry.

    Args:
        name: The name of the widget to create (e.g., "Button").
        *args, **kwargs: Arguments to pass to the widget's constructor.

    Returns:
        An instance of the registered widget.
        
    Raises:
        ValueError: If the widget name is not found in the registry.
    """
    widget_class = _WIDGET_REGISTRY.get(name)
    if not widget_class:
        raise ValueError(f"Widget type '{name}' not found in registry. Have you registered it?")
    
    return widget_class(*args, **kwargs) 