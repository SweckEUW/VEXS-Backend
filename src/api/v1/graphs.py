
from fastapi import APIRouter, HTTPException
from typing import List
from src.models.graph import GraphCreate, GraphResponse
from src.services import flowpipe_service, shotgrid_service

router = APIRouter()

# Execute test graph
@router.get("/executeTest")
def execute_test_graph():
    # Run evaluation via flowpipe service
    success = flowpipe_service.evaluate_test_graph()
    
    return {"status": success}

# Fetch all graphs
@router.get("/", response_model=List[GraphResponse])
def list_graphs():
    graphs = shotgrid_service.get_all_graphs()
    if not graphs: return []
    return graphs

# Fetch single graph
@router.get("/{graph_id}", response_model=GraphResponse)
def get_graph(graph_id: int):
    graph = shotgrid_service.get_graph(graph_id)
    if not graph: raise HTTPException(status_code=404, detail="Graph not found")
    return graph

# Create new graph
@router.post("/", response_model=GraphResponse)
def create_graph(payload: GraphCreate):
    new_graph = shotgrid_service.create_graph(payload)
    if not new_graph: raise HTTPException(status_code=400, detail="Creation failed")
    return new_graph



# update graph
@router.put("/{graph_id}", response_model=GraphResponse)
def update_graph(graph_id: int, payload: GraphCreate):
    updated_graph = shotgrid_service.update_graph(graph_id, payload)
    if not updated_graph: raise HTTPException(status_code=400, detail="Update failed")
    return updated_graph

# Delete graph by id
@router.delete("/{graph_id}")
def delete_graph(graph_id: int):
    success = shotgrid_service.delete_graph(graph_id)
    if not success: raise HTTPException(status_code=400, detail="Deletion failed")
    return {"message": "Graph deleted successfully"}

# Execute graph by id
# @router.post("/{graph_id}/execute")
# def execute_graph(graph_id: int):
#     # Fetch graph data from ShotGrid
#     graph_data = shotgrid_service.get_graph(graph_id)
#     if not graph_data: raise HTTPException(status_code=404, detail="Graph not found")
    
#     # Run evaluation via flowpipe service
#     success = flowpipe_service.evaluate_graph(graph_data["flowpipe_graph"])
#     if not success: raise HTTPException(status_code=500, detail="Graph execution failed")
    
#     return {"status": "executed", "graph_id": graph_id}
