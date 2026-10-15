
from fastapi import APIRouter, HTTPException
from typing import List
from src.models.vexsHookConnection import VexsHookConnectionResponse, VexsHookConnectionCreate
from src.services import vexsHookConnectionService
from src.services.vexsHookConnectionService import HookConnectionExistsError

router = APIRouter()

# Fetch all graphs
@router.get("/", response_model=List[VexsHookConnectionResponse])
def list_graphs():
    return vexsHookConnectionService.get_all_hook_connections() or []

# Fetch single graph
@router.get("/{connection_id}", response_model=VexsHookConnectionResponse)
def get_graph(connection_id: int):
    connection = vexsHookConnectionService.get_hook_connection(connection_id)
    if not connection: return None
    return connection

# Fetch all connections of a vexs graph
@router.get("/vexsgraph/{vexsGraph_id}", response_model=List[VexsHookConnectionResponse])
def list_connections_from_vexsGraph(vexsGraph_id: int):
    return vexsHookConnectionService.get_hook_connections_from_vexsGraph(vexsGraph_id)

# Fetch all connections of a vexs hook
@router.get("/vexshook/{vexsHook_id}", response_model=List[VexsHookConnectionResponse])
def list_connections_from_vexsHook(vexsHook_id: int):
    return vexsHookConnectionService.get_hook_connections_from_vexsHook(vexsHook_id)

# Create new graph
@router.post("/", response_model=VexsHookConnectionResponse)
def create_graph(payload: VexsHookConnectionCreate):
    try:
        new_graph = vexsHookConnectionService.create_hook_connection(payload)
    except HookConnectionExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not new_graph: raise HTTPException(status_code=400, detail="Creation failed")
    return new_graph

# Delete graph by id
@router.delete("/{connection_id}")
def delete_graph(connection_id: int):
    success = vexsHookConnectionService.delete_hook_connection(connection_id)
    if not success: raise HTTPException(status_code=400, detail="Deletion failed")
    return {"message": "Graph deleted successfully"}