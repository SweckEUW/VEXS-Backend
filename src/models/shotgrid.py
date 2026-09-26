from datetime import datetime
from typing import TypedDict

class ShotGridEntityRef(TypedDict):
    type: str
    id: int

class ShotGridUserRef(ShotGridEntityRef):
    name: str

class ShotGridGraphEntity(TypedDict):
    type: str
    id: int
    code: str | None
    description: str | None
    sg_json_graph: str | None
    created_at: datetime
    updated_at: datetime
    created_by: ShotGridUserRef | None
    updated_by: ShotGridUserRef | None

class ShotGridGraphData(TypedDict, total=False):
    code: str
    description: str
    sg_json_graph: str
    project: ShotGridEntityRef