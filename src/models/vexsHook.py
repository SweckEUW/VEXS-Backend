from pydantic import BaseModel, Field
from src.models.vexsGraph import ExecutionMode, VexsGraphExecutionResponse

class VexsHook(BaseModel):
    id: int = Field(..., description="ShotGrid entity ID")
    name: str = Field(..., description="Display name of the hook")
    description: str = Field("", description="Description of what the hook does")
    icon: str = Field("", description="Icon representing the hook")

class VexsHookResponse(VexsHook):
    pass

class VexsHookGraphExecutionResult(BaseModel):
    graph_id: int = Field(..., description="ID of the executed vexs graph")
    graph_name: str = Field(..., description="Name of the executed vexs graph")
    execution: VexsGraphExecutionResponse | None = Field(default=None, description="Execution result, set on success")
    error: str | None = Field(default=None, description="Error message, set on failure")

class VexsHookExecutionResponse(BaseModel):
    hook_id: int = Field(..., description="ID of the executed hook")
    mode: ExecutionMode
    results: list[VexsHookGraphExecutionResult] = Field(..., description="Result per connected graph")
