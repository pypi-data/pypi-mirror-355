from .core.window import _winup_app, Window
from .core.component import component
from .core.events import event_bus as events
from .core.hot_reload import hot_reload
from .core.memoize import memo, clear_memo_cache
from typing import Optional

from . import ui
from .style import styler as style
from .state import state
from .tools import wintools, profiler
from . import shell
from . import tasks

# --- Main API ---

def run(main_component: callable, title="WinUp App", width=800, height=600, icon=None, dev=False, menu_bar: Optional[shell.MenuBar] = None, tool_bar: Optional[shell.ToolBar] = None, status_bar: Optional[shell.StatusBar] = None, tray_icon: Optional[shell.SystemTrayIcon] = None):
    """
    The main entry point for a WinUp application.
    ... (docstring) ...
    Args:
        ...
        dev (bool): If True, enables development features like hot reloading.
        # --- ADD THESE ARGS TO DOCSTRING ---
        menu_bar (shell.MenuBar): A MenuBar object for the main window.
        tool_bar (shell.ToolBar): A ToolBar object for the main window.
        status_bar (shell.StatusBar): A StatusBar object for the main window.
        tray_icon (shell.SystemTrayIcon): An icon for the system tray.
    """
    main_widget = main_component()
    
    # --- ADD THIS ---
    shell_kwargs = {
        "menu_bar": menu_bar,
        "tool_bar": tool_bar,
        "status_bar": status_bar,
    }

    # Pass shell components to the main window factory
    main_window = _winup_app.create_main_window(main_widget, title, width, height, icon, **shell_kwargs)
    
    # Initialize all modules that require a window instance
    style.init_app(_winup_app.app)
    wintools.init_app(main_window)
    
    # Enable hot reloading if in dev mode
    if dev:
        import inspect
        file_to_watch = inspect.getfile(main_component)
        
        def on_reload():
            # This is a simple reload. It replaces the entire central widget.
            new_widget = main_component()
            main_window.setCentralWidget(new_widget)
        
        hot_reload(file_to_watch, on_reload)

    # Run the application event loop
    _winup_app.run()


__all__ = [
    "run", "Window", "hot_reload", "events", 
    "ui", "style", "state", "tools", "profiler",
    "component", "memo", "clear_memo_cache",
    "shell", "tasks"
]
