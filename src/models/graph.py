from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional

# Base properties
class GraphBase(BaseModel):
    name: str = Field(..., description="Name of the VEXS graph")
    # flowpipe_graph: Dict[str, Any] = Field(..., description="Serialized flowpipe graph as JSON")
    flowpipe_graph: str = Field(..., description="Serialized flowpipe graph as JSON")

# Model for POST requests
class GraphCreate(GraphBase):
    pass

# Model for PATCH/PUT requests
class GraphUpdate(BaseModel):
    name: Optional[str] = None
    flowpipe_graph: Optional[Dict[str, Any]] = None

class GraphResponse(GraphBase):
    id: int = Field(..., description="ShotGrid entity ID")

    class Config:
        from_attributes = True # Allow mapping from ORM/Dict