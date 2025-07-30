from .widgets.frame import Frame
from .layout_managers import VBox, HBox

class Column(Frame):
    """A Frame that arranges child widgets vertically using a VBox layout."""
    def __init__(self, children: list = None, props: dict = None, **kwargs):
        # Separate frame props from layout props
        frame_props = props.copy() if props else {}
        layout_props = {
            "alignment": frame_props.pop("alignment", None),
            "spacing": frame_props.pop("spacing", None),
            "margin": frame_props.pop("margin", None)
        }
        layout_props = {k: v for k, v in layout_props.items() if v is not None}
        
        super().__init__(props=frame_props, **kwargs)
        
        self.set_layout(VBox(props=layout_props))
        if children:
            for child in children:
                self.add_child(child)

class Row(Frame):
    """A Frame that arranges child widgets horizontally using an HBox layout."""
    def __init__(self, children: list = None, props: dict = None, **kwargs):
        # Separate frame props from layout props
        frame_props = props.copy() if props else {}
        layout_props = {
            "alignment": frame_props.pop("alignment", None),
            "spacing": frame_props.pop("spacing", None),
            "margin": frame_props.pop("margin", None)
        }
        layout_props = {k: v for k, v in layout_props.items() if v is not None}
        
        super().__init__(props=frame_props, **kwargs)

        self.set_layout(HBox(props=layout_props))
        if children:
            for child in children:
                self.add_child(child) 