from typing import cast
from src.core.config import settings
from src.services import shotgridService, vexsGraphService
from src.models.shotgrid import (ShotGridEntityRef, ShotGridHookConnectionData, ShotGridHookConnectionEntity)
from src.models.vexsHookConnection import (VexsHookConnectionCreate, VexsHookConnectionResponse, VexsHookConnectionUpdate)

HOOK_CONNECTION_ENTITY = settings.shotgrid_hook_connection_entity
GRAPH_ENTITY = settings.shotgrid_graph_entity

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
def _map_to_shotgrid(payload: VexsHookConnectionCreate | VexsHookConnectionUpdate) -> ShotGridHookConnectionData:
    graph_link: ShotGridEntityRef = {"type": GRAPH_ENTITY, "id": payload.flowpipe_graph_id}

    data: ShotGridHookConnectionData = {
        "code": payload.hook.name,
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


# TODO: for graphs overview
# def get_hook_connections_from_vexsGraph(vexsGraph_id: int) -> VexsHookConnectionResponse | None:
#     connection = shotgridService.find_one(HOOK_CONNECTION_ENTITY, connection_id, HOOK_CONNECTION_FIELDS)
#     if not connection:
#         return None

#     return _map_to_pydantic(cast(ShotGridHookConnectionEntity, connection))

# TODO: for hooks overview
# def get_hook_connections_from_vexsHook(vexsHook_id: int) -> VexsHookConnectionResponse | None:
#     connection = shotgridService.find_one(HOOK_CONNECTION_ENTITY, connection_id, HOOK_CONNECTION_FIELDS)
#     if not connection:
#         return None

#     return _map_to_pydantic(cast(ShotGridHookConnectionEntity, connection))

# Create new hook connection
def create_hook_connection(payload: VexsHookConnectionCreate) -> VexsHookConnectionResponse | None:
    data = _map_to_shotgrid(payload)

    new_connection = shotgridService.create(HOOK_CONNECTION_ENTITY, data, HOOK_CONNECTION_FIELDS)
    if not new_connection:
        return None

    return _map_to_pydantic(cast(ShotGridHookConnectionEntity, new_connection))

# Update hook connection
def update_hook_connection( connection_id: int, payload: VexsHookConnectionUpdate) -> VexsHookConnectionResponse | None:
    data = _map_to_shotgrid(payload)

    shotgridService.update(HOOK_CONNECTION_ENTITY, connection_id, data)
    return get_hook_connection(connection_id)

# Delete hook connection
def delete_hook_connection(connection_id: int) -> bool:
    success = shotgridService.delete(HOOK_CONNECTION_ENTITY, connection_id)
    if not success:
        return False

    return True