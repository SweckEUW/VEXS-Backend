from fastapi import APIRouter, HTTPException
from src.models.vexsGraph import ExecutionMode, VexsGraphExecutionRequest
from src.models.vexsHook import VexsHook, VexsHookExecutionResponse, VexsHookResponse
from src.services import vexsHookConnectionService, vexsHookService

router = APIRouter()

# Fetch all hooks
@router.get("/", response_model=list[VexsHookResponse])
def list_hooks() -> list[VexsHook]:
    return vexsHookService.get_all_hooks() or []

# Fetch single hook
@router.get("/{hook_id}", response_model=VexsHookResponse)
def get_hook(hook_id: int) -> VexsHook:
    hook = vexsHookService.get_hook(hook_id)
    if not hook: raise HTTPException(status_code=404, detail="Hook not found")
    return hook

# Execute all graphs connected to the hook on the server (deadline: not implemented yet)
@router.post("/{hook_id}/execute", response_model=VexsHookExecutionResponse)
def execute_hook(hook_id: int, mode: ExecutionMode = "local", payload: VexsGraphExecutionRequest | None = None):
    hook = vexsHookService.get_hook(hook_id)
    if not hook: raise HTTPException(status_code=404, detail="Hook not found")

    results = vexsHookConnectionService.execute_graphs_from_vexsHook(hook_id, mode, payload.inputs if payload else None)
    return VexsHookExecutionResponse(hook_id=hook_id, mode=mode, results=results)