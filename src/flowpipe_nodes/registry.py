import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Type
from flowpipe import INode
from src.models.flowpipe import SerializedFlowpipeNode

NODE_REGISTRY: Dict[str, Type[INode]] = {}

def register_node(node_type: str):
    # Register node class in central dict
    def decorator(cls: Type[INode]):
        NODE_REGISTRY[node_type] = cls
        cls.node_type = node_type
        return cls
    return decorator

def discover_nodes():
    # Scan and import modules from nodes folder
    nodes_dir = Path(__file__).parent / "nodes"
    if not nodes_dir.exists(): return

    for _, module_name, is_pkg in pkgutil.iter_modules([str(nodes_dir)]):
        if is_pkg: continue
        importlib.import_module(f"src.flowpipe_nodes.nodes.{module_name}")

def get_registered_node_definitions() -> list[SerializedFlowpipeNode]:
    catalog: list[SerializedFlowpipeNode] = []
    
    for node_type, cls in NODE_REGISTRY.items():
        # Instantiate detached from default graph to prevent memory leaks
        probe: INode = cls(name=cls.__name__, graph=None)
        data = probe.to_json()
        
        # Inject UI keys into metadata
        data["metadata"].update({
            "type": node_type,
            "label": getattr(cls, "label", cls.__name__),
            "category": getattr(cls, "category", "General"),
        })
        
        catalog.append(SerializedFlowpipeNode.model_validate(data))
        
    return catalog