from PySide6.QtWidgets import QWidget, QLineEdit, QCheckBox

class StateManager:
    """A centralized state management system for WinUp applications."""

    def __init__(self):
        self._state = {}
        # Stores bindings: {'state_key': [(widget, 'property_name'), ...]}
        self._bindings = {}
        # Stores subscriptions: {'state_key': [callback1, callback2, ...]}
        self._subscriptions = {}

    def set(self, key: str, value):
        """
        Sets a value in the state and updates all bound widgets and subscriptions.
        """
        if self._state.get(key) == value:
            return # No change, no update needed

        self._state[key] = value
        self._update_bindings(key)
        self._execute_subscriptions(key)

    def get(self, key: str, default=None):
        """Gets a value from the state."""
        return self._state.get(key, default)

    def subscribe(self, key: str, callback: callable):
        """
        Subscribes a callback function to a state key. The callback will be
        executed whenever the state value changes.

        The callback will be immediately called with the current value upon subscription.
        """
        if key not in self._subscriptions:
            self._subscriptions[key] = []
        self._subscriptions[key].append(callback)
        # Immediately call with current value
        callback(self.get(key))

    def bind_two_way(self, widget: QWidget, state_key: str):
        """
        Creates a two-way data binding between a widget and a state key.
        The widget will update the state, and the state will update the widget.
        """
        # Determine the property and signal based on widget type
        if isinstance(widget, QLineEdit):
            prop_name = "text"
            signal = widget.textChanged
        elif isinstance(widget, QCheckBox):
            prop_name = "checked"
            signal = widget.stateChanged
        else:
            raise TypeError(f"Widget type '{type(widget).__name__}' does not support two-way binding.")

        # 1. State -> Widget binding (like the normal bind)
        self.bind(widget, prop_name, state_key)
        
        # 2. Widget -> State binding
        # When the widget's signal is emitted, update the state
        signal.connect(lambda value: self.set(state_key, value))

    def bind(self, widget: QWidget, property_name: str, state_key: str):
        """
        Binds a widget's property to a key in the state.

        When the state key is updated via `set()`, the widget's property
        will be automatically updated with the new value.

        Args:
            widget: The UI widget to bind (e.g., a Label, Input).
            property_name: The name of the widget's property to update (e.g., 'text', 'checked').
            state_key: The key in the state store to bind to.
        """
        # Set the initial value on the widget
        initial_value = self.get(state_key)
        if initial_value is not None:
            self._set_widget_property(widget, property_name, initial_value)
        
        # Register the binding for future updates
        if state_key not in self._bindings:
            self._bindings[state_key] = []
        self._bindings[state_key].append((widget, property_name))

    def _update_bindings(self, key: str):
        """Update all widgets bound to a specific state key."""
        if key not in self._bindings:
            return

        new_value = self.get(key)
        for widget, property_name in self._bindings[key]:
            self._set_widget_property(widget, property_name, new_value)
            
            # Repolish to apply any style changes if needed
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _execute_subscriptions(self, key: str):
        """Execute all callbacks subscribed to a specific state key."""
        if key in self._subscriptions:
            new_value = self.get(key)
            for callback in self._subscriptions[key]:
                callback(new_value)

    def _set_widget_property(self, widget, property_name, value):
        """Helper to set a property on a widget, trying setter method first."""
        setter = getattr(widget, f"set{property_name.capitalize()}", None)
        if setter and callable(setter):
            setter(value)
        else:
            widget.setProperty(property_name.encode(), value)
        
        widget.style().unpolish(widget)
        widget.style().polish(widget)
