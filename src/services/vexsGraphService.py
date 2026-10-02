from src.core.config import settings
from src.services import shotgridService
from src.models.shotgrid import ShotGridEntityRef, ShotGridFilter, ShotGridGraphEntity, ShotGridGraphData
from src.models.vexsGraph import VexsGraphCreate, VexsGraphResponse, VexsGraphUpdate
from src.models.flowpipe import SerializedFlowpipeGraph

GRAPH_ENTITY = settings.shotgrid_graph_entity
HOOK_CONNECTION_ENTITY = settings.shotgrid_hook_connection_entity
GRAPH_FIELDS = ["id", "code", "description", "sg_json_graph", "created_at", "updated_at"]

from typing import cast

# Map ShotGrid data to API structure
def _map_to_pydantic(sg_graph: ShotGridGraphEntity) -> VexsGraphResponse:
    raw_graph = sg_graph["sg_json_graph"]

    flowpipe_graph = None
    if raw_graph:
        flowpipe_graph = SerializedFlowpipeGraph.model_validate_json(raw_graph)

    return VexsGraphResponse(
        id=sg_graph["id"],
        name=sg_graph["code"],
        description=sg_graph["description"],
        flowpipe_graph=flowpipe_graph,
        created_at=sg_graph["created_at"],
        updated_at=sg_graph["updated_at"],
    )

# Map API payload to ShotGrid data (only fields that were set)
def _map_to_shotgrid(payload: VexsGraphCreate | VexsGraphUpdate) -> ShotGridGraphData:
    data: ShotGridGraphData = {}

    if payload.name is not None:
        data["code"] = payload.name
    if payload.description is not None:
        data["description"] = payload.description
    if payload.flowpipe_graph is not None:
        data["sg_json_graph"] = payload.flowpipe_graph.model_dump_json(exclude_unset=True)

    return data

# Fetch all graphs
def get_all_graphs() -> list[VexsGraphResponse]:
    graphs = shotgridService.find(GRAPH_ENTITY, GRAPH_FIELDS)
    if not graphs:
        return []

    sg_graphs = cast(list[ShotGridGraphEntity], graphs)
    return [_map_to_pydantic(graph) for graph in sg_graphs]

# Fetch single graph
def get_graph(graph_id: int) -> VexsGraphResponse | None:
    graph = shotgridService.find_one(GRAPH_ENTITY, graph_id, GRAPH_FIELDS)
    if not graph:
        return None

    return _map_to_pydantic(cast(ShotGridGraphEntity, graph))

# Create new graph
def create_graph(payload: VexsGraphCreate) -> VexsGraphResponse | None:
    data = _map_to_shotgrid(payload)

    new_graph = shotgridService.create(GRAPH_ENTITY, data, GRAPH_FIELDS)
    if not new_graph:
        return None

    return _map_to_pydantic(cast(ShotGridGraphEntity, new_graph))

# Update graph
def update_graph(graph_id: int, payload: VexsGraphUpdate) -> VexsGraphResponse | None:
    data = _map_to_shotgrid(payload)

    shotgridService.update(GRAPH_ENTITY, graph_id, data)
    return get_graph(graph_id)

# Delete graph together with all hook connections linked to it
def delete_graph(graph_id: int) -> bool:
    graph_link: ShotGridEntityRef = {"type": GRAPH_ENTITY, "id": graph_id}
    filters: list[ShotGridFilter] = [["sg_vexs_graph_1", "is", graph_link]]
    connections = shotgridService.find(HOOK_CONNECTION_ENTITY, fields=["id"], filters=filters)

    entities: list[ShotGridEntityRef] = [{"type": HOOK_CONNECTION_ENTITY, "id": connection["id"]} for connection in connections]
    entities.append(graph_link)

    return shotgridService.batch_delete(entities)