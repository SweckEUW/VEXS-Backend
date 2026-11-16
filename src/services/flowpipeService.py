import logging
import math
import time
from datetime import timedelta
from typing import Any
from flowpipe import Graph
from flowpipe.plug import InputPlug, InputPlugGroup
from src.models.flowpipe import GraphInputType, SerializedFlowpipeGraph
from src.models.vexsGraph import ExecutionMode, VexsGraphExecutionResponse

log = logging.getLogger(__name__)

# None is valid for every type: it is an explicit value, not a missing one (same rules as the editor)
def _is_valid_value(type: GraphInputType, value: Any) -> bool:
    if value is None:
        return True
    if type == "str":
        return isinstance(value, str)
    if type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if type == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    return isinstance(value, bool)

# Validate the passed values against the declared graph inputs and fill in the defaults
def resolve_graph_inputs(data: SerializedFlowpipeGraph, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    inputs = inputs or {}

    unknown = [name for name in inputs if name not in data.inputs]
    if unknown:
        raise ValueError(f"Unknown graph inputs: {', '.join(unknown)}")

    values: dict[str, Any] = {}
    for name, spec in data.inputs.items():
        if name in inputs:
            value = inputs[name]
            if not _is_valid_value(spec.type, value):
                raise ValueError(f"Value {value!r} of graph input '{name}' is not a valid '{spec.type}'")
            values[name] = value
        elif "value" in spec.model_fields_set:
            values[name] = spec.value
        else:
            raise ValueError(f"Graph input '{name}' has no default and no value was passed")

    return values

# Promote the referenced plugs to the graph and set the resolved values on them
def _apply_graph_inputs(graph: Graph, data: SerializedFlowpipeGraph, values: dict[str, Any]) -> None:
    nodes = {node.identifier: node for node in graph.all_nodes}
    claimed: set[InputPlug] = set()

    for name, spec in data.inputs.items():
        plugs: list[InputPlug] = []
        for ref in spec.plugs:
            node = nodes.get(ref.node)
            if node is None:
                raise ValueError(f"Graph input '{name}' references unknown node '{ref.node}'")
            plug = node.all_inputs().get(ref.plug)
            if plug is None:
                raise ValueError(f"Graph input '{name}' references unknown plug '{ref.node}.{ref.plug}'")
            # A node connection wins over a graph input, and the first graph input wins over later ones
            if plug.connections or plug in claimed:
                continue
            claimed.add(plug)
            plugs.append(plug)

        if len(plugs) == 1:
            graph.add_plug(plugs[0], name)
        elif plugs:
            InputPlugGroup(name, graph, plugs)
        else:
            continue
        graph.inputs[name].value = values[name]

# Evaluate graph locally in the backend process
def evaluate_graph(data: SerializedFlowpipeGraph, inputs: dict[str, Any] | None = None) -> Graph:
    values = resolve_graph_inputs(data, inputs)
    graph = Graph.from_json(data.model_dump(exclude_unset=True))
    _apply_graph_inputs(graph, data, values)
    graph.evaluate()
    return graph

# Execute graph locally on the server, deadline is not implemented yet
def execute_graph(data: SerializedFlowpipeGraph, mode: ExecutionMode = "local", inputs: dict[str, Any] | None = None) -> VexsGraphExecutionResponse:
    if mode == "deadline":
        resolve_graph_inputs(data, inputs)  # reject invalid inputs before submitting
        # TODO: Submit graph to the Deadline farm
        return VexsGraphExecutionResponse(mode="deadline", status="skipped")

    start = time.monotonic()
    evaluate_graph(data, inputs)
    log.info("Execution of graph '%s' finished in %s", data.name, timedelta(seconds=int(time.monotonic() - start)))
    return VexsGraphExecutionResponse(mode="local", status="success")
