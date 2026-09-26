from datetime import datetime
from pydantic import (BaseModel, Field)
from src.models.flowpipe import SerializedFlowpipeGraph

class VexsGraphBase(BaseModel):
    name: str = Field(..., description="Name of the VEXS graph")
    description: str | None = Field(None, description="Description of the VEXS graph")
    flowpipe_graph: SerializedFlowpipeGraph = Field(..., description="Serialized flowpipe graph")

class VexsGraphCreate(VexsGraphBase):
    pass

class VexsGraphUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    flowpipe_graph: SerializedFlowpipeGraph | None = None

class VexsGraphResponse(BaseModel):
    id: int = Field(..., description="ShotGrid entity ID")
    name: str | None = None
    description: str | None = None
    flowpipe_graph: SerializedFlowpipeGraph | None = None
    created_at: datetime = Field(..., description="Timestamp of creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")