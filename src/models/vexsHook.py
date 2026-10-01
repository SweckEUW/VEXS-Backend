from pydantic import BaseModel, Field
class VexsHook(BaseModel):
    id: int = Field(..., description="ShotGrid entity ID")
    name: str = Field(..., description="Display name of the hook")
    description: str = Field("", description="Description of what the hook does")

class VexsHookResponse(VexsHook):
    pass