import logging
import os
from typing import Any
import shotgun_api3
from flowpipe import INode, InputPlug, OutputPlug
from src.core.config import settings
from src.flowpipeNodes.registry import register_node

log = logging.getLogger(__name__)

# shotgun_api3 waits forever by default, a stalled connection would block the graph
TIMEOUT_SECS = 60

@register_node("shotgrid.create_version")
class ShotGridCreateVersionNode(INode):
    # UI metadata
    category = "ShotGrid"
    label = "ShotGrid Create Version"
    description = "Creates a Version linked to the task and uploads the movie"
    icon = "https://api.iconify.design/mdi/cloud-upload.svg?color=%233FA9F5"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        InputPlug("shotgrid_task_id", self, value=0)
        InputPlug("slated_mp4", self, value="")
        InputPlug("version_name", self, value="")
        OutputPlug("version_id", self)

    def compute(self, shotgrid_task_id: int, slated_mp4: str, version_name: str) -> dict[str, Any]:
        if not shotgrid_task_id:
            raise ValueError("shotgrid_task_id is required")
        if not slated_mp4 or not os.path.isfile(slated_mp4):
            raise ValueError(f"Movie not found: {slated_mp4}")

        # Connect lazily, so the timeout is already set for the first request
        sg = shotgun_api3.Shotgun(settings.shotgrid_server_path, settings.shotgrid_script_name, settings.shotgrid_script_key, connect=False)
        sg.config.timeout_secs = TIMEOUT_SECS

        log.info("Looking up Task %d", int(shotgrid_task_id))
        task = sg.find_one("Task", [["id", "is", int(shotgrid_task_id)]], ["entity", "project"])
        if not task:
            raise RuntimeError(f"Task {shotgrid_task_id} not found")

        # ShotGrid only accepts a string as code, the plug can also get an int (e.g. a version number)
        code = str(version_name) if version_name else os.path.splitext(os.path.basename(slated_mp4))[0]
        # Project comes from the task, so the graph works across projects
        log.info("Creating Version '%s' for Task %d", code, task["id"])
        version = sg.create("Version", {
            "project": task["project"],
            "code": code,
            "sg_task": {"type": "Task", "id": task["id"]},
            "entity": task["entity"],
            "sg_path_to_movie": slated_mp4,
        })
        log.info("Created Version %d", version["id"])

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
