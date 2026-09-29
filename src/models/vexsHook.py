from enum import Enum
from pydantic import BaseModel, Field

class HookType(str, Enum):
    ON_ASSET_PUBLISH = "onAssetPublish"
    ON_SHOT_PUBLISH = "onShotPublish"
    ON_TASK_COMPLETE = "onTaskComplete"
    ON_TASK_UPDATE = "onTaskUpdate"
    ON_TASK_CREATE = "onTaskCreate"
    ON_TASK_DELETE = "onTaskDelete"
    ON_VERSION_CREATE = "onVersionCreate"
    ON_VERSION_UPDATE = "onVersionUpdate"
    ON_VERSION_DELETE = "onVersionDelete"

Hooks = [h.value for h in HookType]

class Hook(BaseModel):
    id: int = Field(..., description="ShotGrid entity ID")
    name: str = Field(..., description="Display name of the hook")
    description: str = Field("", description="Description of what the hook does")
    type: HookType = Field(..., description="VEXS hook event type")
