import os
import shotgun_api3
from flowpipe import INode, InputPlug, OutputPlug
from src.core.config import settings
from src.flowpipeNodes.registry import register_node

@register_node("shotgrid.create_version")
class ShotGridCreateVersionNode(INode):
    # UI metadata
    category = "ShotGrid"
    label = "ShotGrid Create Version"
    description = "Creates a Version linked to the task and uploads the movie"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        InputPlug("task_id", self, value=0)
        InputPlug("slated_mp4", self, value="")
        InputPlug("version_name", self, value="")
        OutputPlug("version_id", self)

    def compute(self, task_id: int, slated_mp4: str, version_name: str) -> dict:
        if not task_id:
            raise ValueError("task_id is required")
        if not slated_mp4 or not os.path.isfile(slated_mp4):
            raise ValueError(f"Movie not found: {slated_mp4}")

        sg = shotgun_api3.Shotgun(settings.shotgrid_server_path, settings.shotgrid_script_name, settings.shotgrid_script_key)

        task = sg.find_one("Task", [["id", "is", int(task_id)]], ["entity"])
        if not task:
            raise RuntimeError(f"Task {task_id} not found")

        version = sg.create("Version", {
            "project": {"type": "Project", "id": settings.shotgrid_project_id},
            "code": version_name or os.path.splitext(os.path.basename(slated_mp4))[0],
            "sg_task": {"type": "Task", "id": task["id"]},
            "entity": task["entity"],
            "sg_path_to_movie": slated_mp4,
        })

        # Remove the version again if the upload fails, so no empty version stays behind
        try:
            sg.upload("Version", version["id"], slated_mp4, field_name="sg_uploaded_movie")
        except Exception:
            sg.delete("Version", version["id"])
            raise

        return {"version_id": version["id"]}
