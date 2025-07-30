import sys
from PySide6.QtWidgets import QApplication, QWidget, QSizePolicy

class Styler:
    def __init__(self):
        self._app: QApplication = None
        self._definitions = {}
        self._styled_widgets = {}

    def init_app(self, app: QApplication):
        """Stores the application instance to apply global styles."""
        self._app = app

    def add_style_dict(self, styles: dict):
        """
        Adds a dictionary of styles to the application.
        The dictionary is converted to a QSS string and applied globally.
        """
        if not self._app:
            print("Warning: Styler has not been initialized with a QApplication instance. "
                  "Call init_app(app) first.", file=sys.stderr)
            return

        # Deep merge the new styles into the existing definitions
        for selector, rules in styles.items():
            if selector not in self._definitions:
                self._definitions[selector] = {}
            self._definitions[selector].update(rules)
        
        qss = self._to_qss(self._definitions)
        self._app.setStyleSheet(qss)

    def add_style(self, widget, style_class: str):
        """
        Applies a style class to a widget. This allows targeting widgets
        with QSS property selectors, e.g., `[class~="primary"]`.
        """
        current_classes = widget.property("class") or ""
        # Avoid adding duplicate classes
        if style_class not in current_classes.split():
            new_classes = f"{current_classes} {style_class}".strip()
            widget.setProperty("class", new_classes)
            self._repolish(widget)

    def set_id(self, widget, id_name: str):
        """Sets the object name for a widget, allowing it to be targeted with an ID selector."""
        widget.setObjectName(id_name)
        self._repolish(widget)

    def set_fixed_size(self, widget: QWidget, horizontal: bool = True, vertical: bool = True):
        """
        Prevents a widget from stretching during layout.

        Args:
            widget: The widget to modify.
            horizontal: If True, the widget will not stretch horizontally.
            vertical: If True, the widget will not stretch vertically.
        """
        policy = widget.sizePolicy()
        
        h_policy = QSizePolicy.Policy.Fixed if horizontal else QSizePolicy.Policy.Preferred
        v_policy = QSizePolicy.Policy.Fixed if vertical else QSizePolicy.Policy.Preferred
        
        policy.setHorizontalPolicy(h_policy)
        policy.setVerticalPolicy(v_policy)
        
        widget.setSizePolicy(policy)

    def toggle_class(self, widget: QWidget, class_name: str, condition: bool):
        """
        Adds or removes a class from a widget based on a condition.
        This is the recommended way to toggle styles dynamically.
        """
        current_classes = (widget.property("class") or "").split()
        
        # Add or remove the class based on the condition
        if condition and class_name not in current_classes:
            current_classes.append(class_name)
        elif not condition and class_name in current_classes:
            current_classes.remove(class_name)
            
        widget.setProperty("class", " ".join(current_classes))
        self._repolish(widget)

    def _to_qss(self, styles: dict) -> str:
        """Converts a style dictionary to a QSS string."""
        parts = []
        for selector, rules in styles.items():
            rules_str = "; ".join(f"{prop}: {val}" for prop, val in rules.items())
            parts.append(f"{selector} {{ {rules_str}; }}")
        return "\n".join(parts)

    def _repolish(self, widget):
        """Triggers a style re-computation for the widget."""
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def apply_props(self, widget, props: dict):
        """Applies a dictionary of properties to a widget."""
        if not self._app:
            print("Warning: Styler has not been initialized. Call init_app(app) first.", file=sys.stderr)
            # Even if not initialized, we can still try to apply direct styles.

        # Handle special properties first
        if "class" in props:
            self.add_style(widget, props.pop("class"))
        if "id" in props:
            self.set_id(widget, props.pop("id"))

        # The rest of the props are assumed to be direct CSS properties
        style_str = ""
        for key, value in props.items():
            css_key = key.replace('_', '-')
            style_str += f"{css_key}: {value};"

        if style_str:
            # Append to existing stylesheet to avoid overwriting class/id styles
            existing_style = widget.styleSheet() or ""
            if existing_style and not existing_style.endswith(';'):
                existing_style += ';'
            widget.setStyleSheet(existing_style + " " + style_str)

# Singleton instance
styler = Styler() 