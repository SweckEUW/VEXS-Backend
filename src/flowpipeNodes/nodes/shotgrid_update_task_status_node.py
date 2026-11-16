import logging
from typing import Any
import shotgun_api3
from flowpipe import INode, InputPlug, OutputPlug
from src.core.config import settings
from src.flowpipeNodes.registry import register_node

log = logging.getLogger(__name__)

# shotgun_api3 waits forever by default, a stalled connection would block the graph
TIMEOUT_SECS = 60

@register_node("shotgrid.update_task_status")
class ShotGridUpdateTaskStatusNode(INode):
    # UI metadata
    category = "ShotGrid"
    label = "ShotGrid Update Task Status"
    description = "Sets the task status, runs only after a version was created"
    icon = "https://api.iconify.design/mdi/flag-checkered.svg?color=%233FA9F5"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        InputPlug("shotgrid_task_id", self, value=0)
        # Only used as dependency, so the status changes after a successful upload
        InputPlug("version_id", self, value=0)
        InputPlug("status", self, value="crea")
        OutputPlug("success", self)

    def compute(self, shotgrid_task_id: int, version_id: int, status: str) -> dict[str, Any]:
        if not shotgrid_task_id:
            raise ValueError("shotgrid_task_id is required")
        if not version_id:
            raise ValueError("version_id is missing, task status is not changed")
        if not status:
            raise ValueError("status is required")

        # Connect lazily, so the timeout is already set for the first request
        sg = shotgun_api3.Shotgun(settings.shotgrid_server_path, settings.shotgrid_script_name, settings.shotgrid_script_key, connect=False)
        sg.config.timeout_secs = TIMEOUT_SECS

        log.info("Setting status of Task %d to '%s' (after Version %d)", int(shotgrid_task_id), status, int(version_id))
        record = sg.update("Task", int(shotgrid_task_id), {"sg_status_list": status})
        log.info("Set status of Task %d to '%s'", int(shotgrid_task_id), status)

        return {"success": bool(record)}
