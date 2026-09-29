from datetime import datetime
from typing import Any, TypeAlias, TypedDict

# Raw record as returned by shotgun_api3
ShotGridRecord: TypeAlias = dict[str, Any]

# Single filter condition, e.g. ["id", "is", 42]
ShotGridFilter: TypeAlias = list[Any]

class ShotGridEntityRef(TypedDict):
    type: str
    id: int

class ShotGridUserRef(ShotGridEntityRef):
    name: str
class ShotGridEntityBase(TypedDict):
    type: str
    id: int
    code: str | None
    created_at: datetime
    updated_at: datetime
    created_by: ShotGridUserRef | None
    updated_by: ShotGridUserRef | None


# Graphs
class ShotGridGraphEntity(ShotGridEntityBase):
    sg_json_graph: str | None
    description: str | None

class ShotGridGraphData(TypedDict, total=False):
    code: str
    description: str
    sg_json_graph: str


# Hook Connections
class ShotGridHookConnectionEntity(ShotGridEntityBase):
    sg_flowpipe_graph_id: int
    sg_hook_id: int

class ShotGridHookConnectionData(TypedDict, total=False):
    code: str
    sg_flowpipe_graph_id: ShotGridEntityRef
    sg_hook_id: ShotGridEntityRef