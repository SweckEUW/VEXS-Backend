from flowpipe import Graph
from src.models.flowpipe import SerializedFlowpipeGraph
from src.models.vexsGraph import ExecutionMode, VexsGraphExecutionResponse

# Evaluate graph locally in the backend process
def evaluate_graph(data: SerializedFlowpipeGraph) -> Graph:
    graph = Graph.from_json(data.model_dump(exclude_unset=True))
    graph.evaluate()
    return graph

# Execute graph locally on the server, deadline is not implemented yet
def execute_graph(data: SerializedFlowpipeGraph, mode: ExecutionMode = "local") -> VexsGraphExecutionResponse:
    if mode == "deadline":
        # TODO: Submit graph to the Deadline farm
        return VexsGraphExecutionResponse(mode="deadline", status="skipped")
    
    evaluate_graph(data)
    return VexsGraphExecutionResponse(mode="local", status="success")
