from datetime import datetime
from pydantic import BaseModel, Field
from src.models.vexsGraph import VexsGraphResponse

class VexsHookConnectionBase(BaseModel):
    hook_id: int = Field(..., description="ID of the associated hook")

class VexsHookConnectionCreate(VexsHookConnectionBase):
    vexs_graph_id: int = Field(..., description="ID of the associated vexs graph")

class VexsHookConnectionResponse(VexsHookConnectionBase):
    id: int = Field(..., description="ShotGrid entity ID")
    vexs_graph: VexsGraphResponse = Field(..., description="Associated vexs graph")
    created_at: datetime = Field(..., description="Timestamp of creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")