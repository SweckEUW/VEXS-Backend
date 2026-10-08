from typing import Any
from flowpipe import INode, InputPlug, OutputPlug
from src.flowpipeNodes.registry import register_node

@register_node("string.value")
class StringNode(INode):
    # UI metadata
    category = "String"
    label = "String"
    description = "Outputs a constant string value"
    icon = "https://api.iconify.design/mdi/format-text.svg?color=%239CA3AF"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # Input value acting as parameter
        InputPlug("value", self, value="")
        # Output plug carrying the string
        OutputPlug("value", self)

    def compute(self, value: str) -> dict[str, Any]:
        # Forward value to output
        return {"value": str(value or "")}
