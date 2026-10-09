from fastapi import APIRouter, HTTPException
from typing import List
from src.models.vexsGraph import ExecutionMode, VexsGraphCreate, VexsGraphExecutionResponse, VexsGraphResponse, VexsGraphUpdate
from src.services import flowpipeService, vexsGraphService

router = APIRouter()

# Fetch all graphs
@router.get("/", response_model=List[VexsGraphResponse])
def list_graphs():
    return vexsGraphService.get_all_graphs() or []

# Fetch single graph
@router.get("/{graph_id}", response_model=VexsGraphResponse)
def get_graph(graph_id: int):
    graph = vexsGraphService.get_graph(graph_id)
    if not graph: raise HTTPException(status_code=404, detail="Graph not found")
    return graph

# Create new graph
@router.post("/", response_model=VexsGraphResponse)
def create_graph(payload: VexsGraphCreate):
    new_graph = vexsGraphService.create_graph(payload)
    if not new_graph: raise HTTPException(status_code=400, detail="Creation failed")
    return new_graph

# update graph
@router.put("/{graph_id}", response_model=VexsGraphResponse)
def update_graph(graph_id: int, payload: VexsGraphUpdate):
    updated_graph = vexsGraphService.update_graph(graph_id, payload)
    if not updated_graph: raise HTTPException(status_code=400, detail="Update failed")
    return updated_graph

# Delete graph by id
@router.delete("/{graph_id}")
def delete_graph(graph_id: int):
    success = vexsGraphService.delete_graph(graph_id)
    if not success: raise HTTPException(status_code=400, detail="Deletion failed")
    return {"message": "Graph deleted successfully"}

# Get Graph JSON from Shotgrid and execute it on the server
@router.post("/{graph_id}/execute", response_model=VexsGraphExecutionResponse)
def execute_graph(graph_id: int, mode: ExecutionMode = "local"):
    graph = vexsGraphService.get_graph(graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")

    try:
        return flowpipeService.execute_graph(graph.flowpipe_graph, mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))