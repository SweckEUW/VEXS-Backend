from flowpipe import Graph
from src.models.flowpipe import SerializedFlowpipeGraph

def evaluate_graph(data: SerializedFlowpipeGraph) -> Graph:
    graph = Graph.deserialize(data.model_dump(exclude_unset=True))
    graph.evaluate()
    return graph