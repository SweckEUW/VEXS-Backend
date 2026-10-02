from fastapi import APIRouter, HTTPException
from typing import List, Literal
from src.models.vexsHook import VexsHookExecutionResponse, VexsHookResponse
from src.services import vexsHookConnectionService, vexsHookService

router = APIRouter()

# Fetch all hooks
@router.get("/", response_model=List[VexsHookResponse])
def list_hooks():
    return vexsHookService.get_all_hooks() or []

# Fetch single hook
@router.get("/{hook_id}", response_model=VexsHookResponse)
def get_graph(hook_id: int):
    graph = vexsHookService.get_hook(hook_id)
    if not graph: raise HTTPException(status_code=404, detail="Graph not found")
    return graph

# Execute all graphs connected to the hook on the Deadline farm (or locally on the server)
@router.post("/{hook_id}/execute", response_model=VexsHookExecutionResponse)
def execute_hook(hook_id: int, mode: Literal["deadline", "local"] = "deadline"):
    hook = vexsHookService.get_hook(hook_id)
    if not hook: raise HTTPException(status_code=404, detail="Hook not found")

    results = vexsHookConnectionService.execute_graphs_from_vexsHook(hook_id, mode)
    return VexsHookExecutionResponse(hook_id=hook_id, mode=mode, results=results)
