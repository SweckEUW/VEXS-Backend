# app/pipeline/registry.py
from typing import Dict, Type
from flowpipe import INode

# Central node registry mapping string identifiers to Python classes
NODE_REGISTRY: Dict[str, Type[INode]] = {}

def register_node(node_type: str):
    def decorator(cls: Type[INode]):
        NODE_REGISTRY[node_type] = cls
        return cls
    return decorator