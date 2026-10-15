from typing import List
from fastapi import APIRouter
from src.models.flowpipe import SerializedFlowpipeNode
from src.flowpipeNodes.registry import get_registered_node_definitions

router = APIRouter()

@router.get("/", response_model=List[SerializedFlowpipeNode])
def list_node_definitions():
    return get_registered_node_definitions() or []