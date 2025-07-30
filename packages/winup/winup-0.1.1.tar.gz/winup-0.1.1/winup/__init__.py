from .core.window import _winup_app
from .core.component import component
from .core.events import event_bus as events
from .core.hot_reload import hot_reload

from . import ui
from .style import styler as style
from .state import state
from .tools import wintools, profiler

# --- Main API ---

def run(main_component: callable, title="WinUp App", width=800, height=600, icon=None, dev=False):
    """
    The main entry point for a WinUp application.
    
    Args:
        main_component: A function (ideally a @component) that returns the main widget.
        title, width, height, icon: Standard window properties.
        dev (bool): If True, enables development features like hot reloading.
    """
    _winup_app.create_window(title, width, height, icon)
    
    # Initialize all modules with the app/window instances
    style.init_app(_winup_app.app)
    wintools.init_app(_winup_app._main_window)
    
    # Set the main widget
    main_widget = main_component()
    _winup_app.add_widget(main_widget)
    
    # Enable hot reloading if in dev mode
    if dev:
        import inspect
        file_to_watch = inspect.getfile(main_component)
        
        def on_reload():
            # This is a simple reload. It replaces the entire central widget.
            new_widget = main_component()
            _winup_app.add_widget(new_widget)
        
        hot_reload(file_to_watch, on_reload)

    # Run the application
    _winup_app.show()


__all__ = [
    "run", "hot_reload", "events", 
    "ui", "style", "state", "tools", "profiler",
    "component"
]
