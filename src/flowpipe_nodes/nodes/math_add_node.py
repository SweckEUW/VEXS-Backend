from flowpipe import INode, InputPlug, OutputPlug
from src.flowpipe_nodes.registry import register_node

@register_node("math.number")
class NumberNode(INode):
    # UI metadata
    category = "Math"
    label = "Number"
    description = "Outputs a constant float or integer value"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Input value acting as parameter
        InputPlug("value", self, value=0.0)
        # Output plug carrying the number
        OutputPlug("value", self)

    def compute(self, value: float) -> dict:
        # Forward value to output
        return {"value": float(value or 0.0)}


@register_node("math.add")
class AddNode(INode):
    # UI metadata
    category = "Math"
    label = "Add"
    description = "Adds two numbers together"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Input terms with default 0.0
        InputPlug("a", self, value=0.0)
        InputPlug("b", self, value=0.0)
        # Result output
        OutputPlug("result", self)

    def compute(self, a: float, b: float) -> dict:
        # Sum both inputs safely
        val_a = a if a is not None else 0.0
        val_b = b if b is not None else 0.0
        return {"result": val_a + val_b}