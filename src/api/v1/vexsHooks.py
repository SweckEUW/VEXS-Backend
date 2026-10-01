from http.client import HTTPException
from fastapi import APIRouter
from typing import List
from src.models.vexsHook import VexsHookResponse
from src.services import vexsHookService

router = APIRouter()

# Fetch all hooks
@router.get("/", response_model=List[VexsHookResponse])
def list_hooks():
    hooks = vexsHookService.get_all_hooks()
    if not hooks: return []
    return hooks

# Fetch single hook
@router.get("/{hook_id}", response_model=VexsHookResponse) 
def get_graph(hook_id: int):
    graph = vexsHookService.get_hook(hook_id)
    if not graph: raise HTTPException(status_code=404, detail="Graph not found")
    return graph