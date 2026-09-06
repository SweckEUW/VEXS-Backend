import inspect
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Any

class PlugDefinition(BaseModel):
    # Plug metadata
    name: str
    data_type: str = "any"
    default_value: Optional[Any] = None

class FlowpipeNodeSchema(BaseModel):
    # Complete flowpipe schema for baklava
    type: str
    label: str
    category: str = "General"
    cls: str = Field(..., description="Python class name")
    module: str = Field(..., description="Python module path")
    file_location: str = Field(..., description="Script path on server")
    inputs: List[PlugDefinition]
    outputs: List[PlugDefinition]