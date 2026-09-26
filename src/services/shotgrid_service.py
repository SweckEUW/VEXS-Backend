import shotgun_api3 as shotgun
from src.core.config import settings
from typing import List
from src.models.vexsGraph import VexsGraphCreate, VexsGraphResponse, VexsGraphUpdate
from src.models.flowpipe import SerializedFlowpipeGraph
from src.models.shotgrid import ShotGridGraphData, ShotGridGraphEntity

# Init ShotGrid connection
SHOTGRID_GRAPH_ENTITY = settings.shotgrid_graph_entity
SHOTGRID_PROJECT_ID = settings.shotgrid_project_id
SHOTGRID_SERVER_PATH = settings.shotgrid_server_path
SHOTGRID_SCRIPT_NAME = settings.shotgrid_script_name
SHOTGRID_SCRIPT_KEY = settings.shotgrid_script_key

sg = shotgun.Shotgun(SHOTGRID_SERVER_PATH, SHOTGRID_SCRIPT_NAME, SHOTGRID_SCRIPT_KEY)

# Define internal SG entity name
GRAPH_FIELDS = ["id", "code", "description", "sg_json_graph", "created_at", "updated_at", "created_by", "updated_by"]

# Map SG data to API structure
def _map_to_pydantic(sg_data: ShotGridGraphEntity) -> VexsGraphResponse:
    raw_graph = sg_data["sg_json_graph"]
    return VexsGraphResponse(
        id=sg_data["id"],
        name=sg_data["code"],
        description=sg_data["description"],
        flowpipe_graph=SerializedFlowpipeGraph.model_validate_json(raw_graph) if raw_graph else None,
        created_at=sg_data["created_at"],
        updated_at=sg_data["updated_at"],
    )

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
def get_all_graphs() -> List[VexsGraphResponse]:
    filters = []
    graphs = sg.find(SHOTGRID_GRAPH_ENTITY, filters, GRAPH_FIELDS)
    if not graphs: return []
    return [_map_to_pydantic(g) for g in graphs]

# Fetch single graph
def get_graph(graph_id: int) -> VexsGraphResponse | None:
    filters = [["id", "is", graph_id]]
    graph = sg.find_one(SHOTGRID_GRAPH_ENTITY, filters, GRAPH_FIELDS)
    if not graph: return None
    return _map_to_pydantic(graph)

# Create new graph
def create_graph(payload: VexsGraphCreate) -> VexsGraphResponse:
    data = _map_to_shotgrid(payload)
    data["project"] = {"type": "Project", "id": SHOTGRID_PROJECT_ID}
    new_graph = sg.create(SHOTGRID_GRAPH_ENTITY, data, GRAPH_FIELDS)
    if not new_graph: return None
    return _map_to_pydantic(new_graph)

# Update graph
def update_graph(graph_id: int, payload: VexsGraphUpdate) -> VexsGraphResponse | None:
    data = _map_to_shotgrid(payload)
    sg.update(SHOTGRID_GRAPH_ENTITY, graph_id, data)
    return get_graph(graph_id)

# Delete graph
def delete_graph(graph_id: int) -> bool:
    success = sg.delete(SHOTGRID_GRAPH_ENTITY, graph_id)
    if not success: return False
    return True