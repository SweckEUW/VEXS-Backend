from typing import Literal, cast
from src.core.config import settings
from src.services import flowpipeService, shotgridService, vexsGraphService, vexsHookService
from src.models.shotgrid import (ShotGridEntityRef, ShotGridFilter, ShotGridHookConnectionData, ShotGridHookConnectionEntity)
from src.models.vexsHook import VexsHook, VexsHookGraphExecutionResult
from src.models.vexsHookConnection import (VexsHookConnectionCreate, VexsHookConnectionResponse)

HOOK_CONNECTION_ENTITY = settings.shotgrid_hook_connection_entity
GRAPH_ENTITY = settings.shotgrid_graph_entity

class HookConnectionExistsError(Exception):
    """A connection between this hook and graph already exists."""

# Map ShotGrid data to API structure
def _map_to_pydantic(sg_connection: ShotGridHookConnectionEntity) -> VexsHookConnectionResponse:

    vexs_graph_ref = sg_connection["sg_vexs_graph_1"]
    vexs_graph = vexsGraphService.get_graph(vexs_graph_ref["id"])
    
    return VexsHookConnectionResponse(
        id=sg_connection["id"],
        hook_id=sg_connection["sg_hook_id"],
        vexs_graph=vexs_graph,
        created_at=sg_connection["created_at"],
        updated_at=sg_connection["updated_at"],
    )

# Map API payload to ShotGrid data
def _map_to_shotgrid(payload: VexsHookConnectionCreate, hook: VexsHook) -> ShotGridHookConnectionData:
    graph_link: ShotGridEntityRef = {"type": GRAPH_ENTITY, "id": payload.vexs_graph_id}

    data: ShotGridHookConnectionData = {
        "code": hook.name,
        "sg_vexs_graph_1": graph_link,
        "sg_hook_id": payload.hook_id,
    }
    return data

# Fetch all hook connections
def get_all_hook_connections() -> list[VexsHookConnectionResponse]:
    connections = shotgridService.find(HOOK_CONNECTION_ENTITY)
    if not connections:
        return []

    sg_connections = cast(list[ShotGridHookConnectionEntity], connections)
    return [_map_to_pydantic(connection) for connection in sg_connections]

# Fetch single hook connection
def get_hook_connection(connection_id: int) -> VexsHookConnectionResponse | None:
    connection = shotgridService.find_one(HOOK_CONNECTION_ENTITY, connection_id)
    if not connection:
        return None

    return _map_to_pydantic(cast(ShotGridHookConnectionEntity, connection))

# Fetch all hook connections of a vexs graph
def get_hook_connections_from_vexsGraph(vexsGraph_id: int) -> list[VexsHookConnectionResponse]:
    graph_link: ShotGridEntityRef = {"type": GRAPH_ENTITY, "id": vexsGraph_id}
    filters: list[ShotGridFilter] = [["sg_vexs_graph_1", "is", graph_link]]

    connections = shotgridService.find(HOOK_CONNECTION_ENTITY, filters=filters)
    if not connections:
        return []

    sg_connections = cast(list[ShotGridHookConnectionEntity], connections)
    return [_map_to_pydantic(connection) for connection in sg_connections]

# Fetch all hook connections of a vexs hook
def get_hook_connections_from_vexsHook(vexsHook_id: int) -> list[VexsHookConnectionResponse]:
    filters: list[ShotGridFilter] = [["sg_hook_id", "is", vexsHook_id]]

    connections = shotgridService.find(HOOK_CONNECTION_ENTITY, filters=filters)
    if not connections:
        return []

    sg_connections = cast(list[ShotGridHookConnectionEntity], connections)
    return [_map_to_pydantic(connection) for connection in sg_connections]

# Execute all graphs connected to a vexs hook, a failing graph does not stop the others
def execute_graphs_from_vexsHook(vexsHook_id: int, mode: Literal["deadline", "local"] = "deadline") -> list[VexsHookGraphExecutionResult]:
    results: list[VexsHookGraphExecutionResult] = []

    for connection in get_hook_connections_from_vexsHook(vexsHook_id):
        graph = connection.vexs_graph
        result = VexsHookGraphExecutionResult(graph_id=graph.id, graph_name=graph.name)

        try:
            result.execution = flowpipeService.execute_graph(graph.flowpipe_graph, mode)
        except Exception as exc:
            result.error = str(exc)

        results.append(result)

    return results

# Create new hook connection
def create_hook_connection(payload: VexsHookConnectionCreate) -> VexsHookConnectionResponse | None:
    hook = vexsHookService.get_hook(payload.hook_id)
    if not hook:
        return None

    vexs_graph = vexsGraphService.get_graph(payload.vexs_graph_id)
    if not vexs_graph:
        return None

    # Abort if a connection between this hook and graph already exists
    graph_link: ShotGridEntityRef = {"type": GRAPH_ENTITY, "id": payload.vexs_graph_id}
    filters: list[ShotGridFilter] = [
        ["sg_hook_id", "is", payload.hook_id],
        ["sg_vexs_graph_1", "is", graph_link],
    ]
    if shotgridService.find(HOOK_CONNECTION_ENTITY, fields=["id"], filters=filters):
        raise HookConnectionExistsError(f"Hook {payload.hook_id} is already connected to graph {payload.vexs_graph_id}")

    data = _map_to_shotgrid(payload, hook)

    new_connection = shotgridService.create(HOOK_CONNECTION_ENTITY, data)
    if not new_connection:
        return None

    return _map_to_pydantic(cast(ShotGridHookConnectionEntity, new_connection))

# Delete hook connection
def delete_hook_connection(connection_id: int) -> bool:
    success = shotgridService.delete(HOOK_CONNECTION_ENTITY, connection_id)
    if not success:
        return False

    return True