import inspect
import importlib
import pkgutil
import time
from pathlib import Path
from typing import Dict, Type, List
from flowpipe import INode
from src.models.node import FlowpipeNodeSchema, PlugDefinition

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

def get_registered_node_definitions() -> List[FlowpipeNodeSchema]:
    # Debug current registry size
    print(f"[DEBUG] Registry has {len(NODE_REGISTRY)} nodes registered: {list(NODE_REGISTRY.keys())}")

    definitions: List[FlowpipeNodeSchema] = []
    base_dir = Path(__file__).resolve().parent.parent.parent

    for idx, (node_type, cls) in enumerate(NODE_REGISTRY.items()):
        # Generate unique probe name per request
        unique_probe_name = f"probe_{node_type.replace('.', '_')}_{int(time.time())}_{idx}"
        
        try:
            probe = cls(name=unique_probe_name)
        except Exception as e:
            # Print exact error instead of hiding it
            print(f"[ERROR] Failed to instantiate probe for '{node_type}': {e}")
            continue

        try:
            full_path = Path(inspect.getfile(cls)).resolve()
            rel_path = str(full_path.relative_to(base_dir)).replace("\\", "/")
        except Exception as e:
            print(f"[ERROR] Path resolution failed for '{node_type}': {e}")
            rel_path = str(inspect.getfile(cls)).replace("\\", "/")

        inputs = [
            PlugDefinition(name=name, default_value=plug.value)
            for name, plug in probe.inputs.items()
        ]
        outputs = [
            PlugDefinition(name=name)
            for name in probe.outputs.keys()
        ]

        definitions.append(
            FlowpipeNodeSchema(
                type=node_type,
                label=getattr(cls, "label", node_type),
                category=getattr(cls, "category", "General"),
                cls=cls.__name__,
                module=cls.__module__,
                file_location=rel_path,
                inputs=inputs,
                outputs=outputs
            )
        )

    return definitions