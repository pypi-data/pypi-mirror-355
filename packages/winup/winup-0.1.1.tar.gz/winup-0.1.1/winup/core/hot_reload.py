import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PySide6.QtCore import QObject, Signal

class Reloader(QObject):
    """
    A QObject that emits a signal when a file is changed.
    This is necessary to bridge the watchdog thread with the main GUI thread.
    """
    file_changed = Signal()

class ChangeHandler(FileSystemEventHandler):
    """A handler for file system events that triggers a QObject signal."""
    def __init__(self, reloader: Reloader):
        super().__init__()
        self.reloader = reloader
        self._last_event_time = 0

    def on_modified(self, event):
        # Debounce the event to avoid multiple triggers for one save
        if time.time() - self._last_event_time < 0.5:
            return
        self._last_event_time = time.time()
        
        if not event.is_directory:
            print(f"Hot Reload: Detected change in {event.src_path}. Emitting signal...")
            self.reloader.file_changed.emit()

def hot_reload(file_path: str, callback: callable):
    """
    Sets up a file watcher to trigger a callback on the main GUI thread.
    
    Args:
        file_path: The path to the file to watch.
        callback: The function to call when the file is modified.
    """
    from winup.core.window import _winup_app
    
    # The reloader object must be parented to the main window or app
    # to ensure it lives in the main GUI thread.
    reloader = Reloader(parent=_winup_app.app)
    reloader.file_changed.connect(callback)

    event_handler = ChangeHandler(reloader)
    observer = Observer()
    # Watch the directory of the file, not the file itself, as that is more reliable
    observer.schedule(event_handler, path=os.path.dirname(file_path), recursive=False)
    observer.start()
    
    # The observer runs in a background thread, so this function will not block.
    # We can store the observer on the app object if we need to stop it later.
    if not hasattr(_winup_app, 'observers'):
        _winup_app.observers = []
    _winup_app.observers.append(observer) 