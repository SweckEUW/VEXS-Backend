import logging
import os
from typing import Any
import shotgun_api3
from flowpipe import INode, InputPlug, OutputPlug
from src.core.config import settings
from src.flowpipeNodes.registry import register_node

log = logging.getLogger(__name__)

@register_node("shotgrid.create_version")
class ShotGridCreateVersionNode(INode):
    # UI metadata
    category = "ShotGrid"
    label = "ShotGrid Create Version"
    description = "Creates a Version linked to the task and uploads the movie"
    icon = "https://api.iconify.design/mdi/cloud-upload.svg?color=%233FA9F5"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        InputPlug("task_id", self, value=0)
        InputPlug("slated_mp4", self, value="")
        InputPlug("version_name", self, value="")
        OutputPlug("version_id", self)

    def compute(self, task_id: int, slated_mp4: str, version_name: str) -> dict[str, Any]:
        if not task_id:
            raise ValueError("task_id is required")
        if not slated_mp4 or not os.path.isfile(slated_mp4):
            raise ValueError(f"Movie not found: {slated_mp4}")

        sg = shotgun_api3.Shotgun(settings.shotgrid_server_path, settings.shotgrid_script_name, settings.shotgrid_script_key)

        task = sg.find_one("Task", [["id", "is", int(task_id)]], ["entity"])
        if not task:
            raise RuntimeError(f"Task {task_id} not found")

        code = version_name or os.path.splitext(os.path.basename(slated_mp4))[0]
        version = sg.create("Version", {
            "project": {"type": "Project", "id": settings.shotgrid_project_id},
            "code": code,
            "sg_task": {"type": "Task", "id": task["id"]},
            "entity": task["entity"],
            "sg_path_to_movie": slated_mp4,
        })
        log.info("Created Version %d '%s' for Task %d", version["id"], code, task["id"])

        # Remove the version again if the upload fails, so no empty version stays behind
        log.info("Uploading %s (%.1f MB) to Version %d", slated_mp4, os.path.getsize(slated_mp4) / 1024 ** 2, version["id"])
        try:
            sg.upload("Version", version["id"], slated_mp4, field_name="sg_uploaded_movie")
        except Exception:
            log.warning("Upload failed, deleting Version %d", version["id"])
            sg.delete("Version", version["id"])
            raise

        log.info("Upload to Version %d finished", version["id"])
        return {"version_id": version["id"]}
