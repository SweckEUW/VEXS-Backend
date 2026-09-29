from typing import Any, Mapping
import shotgun_api3
from src.core.config import settings
from src.models.shotgrid import ShotGridEntityRef, ShotGridFilter, ShotGridRecord

# Init ShotGrid connection
SHOTGRID_GRAPH_ENTITY = settings.shotgrid_graph_entity
SHOTGRID_PROJECT_ID = settings.shotgrid_project_id
SHOTGRID_SERVER_PATH = settings.shotgrid_server_path
SHOTGRID_SCRIPT_NAME = settings.shotgrid_script_name
SHOTGRID_SCRIPT_KEY = settings.shotgrid_script_key

_sg = shotgun_api3.Shotgun(SHOTGRID_SERVER_PATH, SHOTGRID_SCRIPT_NAME, SHOTGRID_SCRIPT_KEY)

PROJECT_REF: ShotGridEntityRef = {"type": "Project", "id": settings.shotgrid_project_id}

# Find all entities of a type, optionally filtered
def find(entity_type: str, fields: list[str], filters: list[ShotGridFilter] | None = None) -> list[ShotGridRecord]:
    if filters is None:
        filters = []

    records = _sg.find(entity_type, filters, fields)
    if not records:
        return []

    return records

# Find a single entity by its ID
def find_one(entity_type: str, entity_id: int, fields: list[str]) -> ShotGridRecord | None:
    filters: list[ShotGridFilter] = [["id", "is", entity_id]]

    record = _sg.find_one(entity_type, filters, fields)
    if not record:
        return None

    return record

# Create a new entity in the configured project
def create( entity_type: str, data: Mapping[str, Any], return_fields: list[str]) -> ShotGridRecord | None:
    create_data = dict(data)
    create_data["project"] = PROJECT_REF

    record = _sg.create(entity_type, create_data, return_fields)
    if not record:
        return None

    return record

# Update fields of an existing entity
def update(entity_type: str, entity_id: int, data: Mapping[str, Any]) -> ShotGridRecord | None:
    record = _sg.update(entity_type, entity_id, dict(data))
    if not record:
        return None

    return record

# Delete an entity (ShotGrid moves it to the trash, it can be restored)
def delete(entity_type: str, entity_id: int) -> bool:
    success = _sg.delete(entity_type, entity_id)
    if not success:
        return False

    return True