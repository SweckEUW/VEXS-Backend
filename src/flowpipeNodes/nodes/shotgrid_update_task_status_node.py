import shotgun_api3
from flowpipe import INode, InputPlug, OutputPlug
from src.core.config import settings
from src.flowpipeNodes.registry import register_node

@register_node("shotgrid.update_task_status")
class ShotGridUpdateTaskStatusNode(INode):
    # UI metadata
    category = "ShotGrid"
    label = "ShotGrid Update Task Status"
    description = "Sets the task status, runs only after a version was created"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        InputPlug("task_id", self, value=0)
        # Only used as dependency, so the status changes after a successful upload
        InputPlug("version_id", self, value=0)
        InputPlug("status", self, value="rev")
        OutputPlug("success", self)

    def compute(self, task_id: int, version_id: int, status: str) -> dict:
        if not task_id:
            raise ValueError("task_id is required")
        if not version_id:
            raise ValueError("version_id is missing, task status is not changed")
        if not status:
            raise ValueError("status is required")

        sg = shotgun_api3.Shotgun(settings.shotgrid_server_path, settings.shotgrid_script_name, settings.shotgrid_script_key)
        record = sg.update("Task", int(task_id), {"sg_status_list": status})

        return {"success": bool(record)}
