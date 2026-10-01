from datetime import datetime
from pydantic import BaseModel, Field
from src.models.vexsGraph import VexsGraphResponse

class VexsHookConnectionBase(BaseModel):
    vexs_graph: VexsGraphResponse = Field(..., description="ID of the associated flowpipe graph")
    hook_id: int = Field(..., description="ID of the associated hook")

class VexsHookConnectionCreate(VexsHookConnectionBase):
    pass

class VexsHookConnectionUpdate(VexsHookConnectionBase):
    pass

class VexsHookConnectionResponse(VexsHookConnectionBase):
    id: int = Field(..., description="ShotGrid entity ID")
    created_at: datetime = Field(..., description="Timestamp of creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")