
from fastapi import APIRouter, HTTPException
from typing import List
from src.models.vexsHookConnection import VexsHookConnectionResponse, VexsHookConnectionCreate
from src.services import vexsHookConnectionService

router = APIRouter()

# Fetch all graphs
@router.get("/", response_model=List[VexsHookConnectionResponse])
def list_graphs():
    connections = vexsHookConnectionService.get_all_hook_connections()
    if not connections: return []
    return connections

# Fetch single graph
@router.get("/{connection_id}", response_model=VexsHookConnectionResponse)
def get_graph(connection_id: int):
    connection = vexsHookConnectionService.get_hook_connection(connection_id)
    if not connection: return []
    return connection

# Create new graph
@router.post("/", response_model=VexsHookConnectionResponse)
def create_graph(payload: VexsHookConnectionCreate):
    new_graph = vexsHookConnectionService.create_hook_connection(payload)
    if not new_graph: raise HTTPException(status_code=400, detail="Creation failed")
    return new_graph

# update graph
@router.put("/{connection_id}", response_model=VexsHookConnectionResponse)
def update_graph(connection_id: int, payload: VexsHookConnectionCreate):
    updated_graph = vexsHookConnectionService.update_hook_connection(connection_id, payload)
    if not updated_graph: raise HTTPException(status_code=400, detail="Update failed")
    return updated_graph

# Delete graph by id
@router.delete("/{connection_id}")
def delete_graph(connection_id: int):
    success = vexsHookConnectionService.delete_hook_connection(connection_id)
    if not success: raise HTTPException(status_code=400, detail="Deletion failed")
    return {"message": "Graph deleted successfully"}