
from fastapi import APIRouter, HTTPException
from typing import List
from src.models.vexsGraph import VexsGraphCreate, VexsGraphResponse
from src.services import flowpipe_service, shotgrid_service

router = APIRouter()

# Fetch all graphs
@router.get("/", response_model=List[VexsGraphResponse])
def list_graphs():
    graphs = shotgrid_service.get_all_graphs()
    if not graphs: return []
    return graphs

# Fetch single graph
@router.get("/{graph_id}", response_model=VexsGraphResponse)
def get_graph(graph_id: int):
    graph = shotgrid_service.get_graph(graph_id)
    if not graph: raise HTTPException(status_code=404, detail="Graph not found")
    return graph

# Create new graph
@router.post("/", response_model=VexsGraphResponse)
def create_graph(payload: VexsGraphCreate):
    new_graph = shotgrid_service.create_graph(payload)
    if not new_graph: raise HTTPException(status_code=400, detail="Creation failed")
    return new_graph

# update graph
@router.put("/{graph_id}", response_model=VexsGraphResponse)
def update_graph(graph_id: int, payload: VexsGraphCreate):
    updated_graph = shotgrid_service.update_graph(graph_id, payload)
    if not updated_graph: raise HTTPException(status_code=400, detail="Update failed")
    return updated_graph

# Delete graph by id
@router.delete("/{graph_id}")
def delete_graph(graph_id: int):
    success = shotgrid_service.delete_graph(graph_id)
    if not success: raise HTTPException(status_code=400, detail="Deletion failed")
    return {"message": "Graph deleted successfully"}

# Get Graph JSON from Shotgrid and execute it on server (TODO: On Deadline farm)
@router.post("/{graph_id}/execute")
def execute_graph(graph_id: int):
    graph = shotgrid_service.get_graph(graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")
    if graph.flowpipe_graph is None:
        raise HTTPException(status_code=400, detail="Graph has no flowpipe data")

    flowpipe_service.evaluate_graph(graph.flowpipe_graph)
    return {"status": "success"}