from datetime import datetime
from typing import Any, Literal
from pydantic import (BaseModel, Field)
from src.models.flowpipe import SerializedFlowpipeGraph

# Where a graph is executed, "deadline" is not implemented yet
ExecutionMode = Literal["deadline", "local"]

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

class VexsGraphResponse(VexsGraphBase):
    id: int = Field(..., description="ShotGrid entity ID")
    created_at: datetime = Field(..., description="Timestamp of creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

class VexsGraphExecutionRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict, description="Values for the graph inputs, keyed by input name")

class VexsGraphExecutionResponse(BaseModel):
    mode: ExecutionMode
    status: Literal["success", "skipped"] = Field(..., description="local: evaluated, deadline: not implemented yet")
