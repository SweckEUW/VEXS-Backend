import json
import shotgun_api3 as shotgun
from src.core.config import settings
from typing import List, Dict, Optional
from src.models.graph import GraphCreate

# Init ShotGrid connection
SHOTGRID_GRAPH_ENTITY = settings.shotgrid_graph_entity
SHOTGRID_PROJECT_ID = settings.shotgrid_project_id
SHOTGRID_SERVER_PATH = settings.shotgrid_server_path
SHOTGRID_SCRIPT_NAME = settings.shotgrid_script_name
SHOTGRID_SCRIPT_KEY = settings.shotgrid_script_key

sg = shotgun.Shotgun(SHOTGRID_SERVER_PATH, SHOTGRID_SCRIPT_NAME, SHOTGRID_SCRIPT_KEY)

# Define internal SG entity name
GRAPH_FIELDS = ["id", "code", "sg_json_graph"]

# Map SG data to API structure
def _map_to_pydantic(sg_data: Dict) -> Dict:

    # TODO Parse the JSON string from ShotGrid into a Python dict for the API response
    # raw_json = sg_data.get("sg_json_graph")
    # print("ROHSTRING AUS SHOTGRID:", repr(raw_json))  # Zeigt exakt, was ankommt
    # parsed_graph = json.loads(raw_json) if raw_json else {}

    return {
        "id": sg_data.get("id"),
        "name": sg_data.get("code"),
        "flowpipe_graph": sg_data.get("sg_json_graph")
    }

# Map API structure to SG data
def _map_to_shotgrid(payload: GraphCreate) -> Dict:
    return {
        "code": payload.name,
        # "sg_json_graph": json.dumps(payload.flowpipe_graph)
        "sg_json_graph": payload.flowpipe_graph
    }

# Fetch all graphs
def get_all_graphs() -> List[Dict]:
    filters = []
    graphs = sg.find(SHOTGRID_GRAPH_ENTITY, filters, GRAPH_FIELDS)
    if not graphs: return []
    return [_map_to_pydantic(g) for g in graphs]

# Fetch single graph
def get_graph(graph_id: int) -> Optional[Dict]:
    filters = [["id", "is", graph_id]]
    graph = sg.find_one(SHOTGRID_GRAPH_ENTITY, filters, GRAPH_FIELDS)
    if not graph: return None
    return _map_to_pydantic(graph)

# Create new graph
def create_graph(payload: GraphCreate) -> Optional[Dict]:
    data = _map_to_shotgrid(payload)
    new_graph = sg.create(SHOTGRID_GRAPH_ENTITY, data)
    if not new_graph: return None
    # Map the newly created graph right back for the API response
    return _map_to_pydantic(new_graph)

# Update graph
def update_graph(graph_id: int, payload: GraphCreate) -> Optional[Dict]:
    data = _map_to_shotgrid(payload)
    updated_graph = sg.update(SHOTGRID_GRAPH_ENTITY, graph_id, data)
    if not updated_graph: return None
    return _map_to_pydantic(updated_graph)

# Delete graph
def delete_graph(graph_id: int) -> bool:
    success = sg.delete(SHOTGRID_GRAPH_ENTITY, graph_id)
    if not success: return False
    return True