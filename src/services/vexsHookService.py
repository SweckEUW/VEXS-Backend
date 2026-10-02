from src.models.vexsHook import VexsHook

HOOKS: list[VexsHook] = [
    VexsHook(
        id=1,
        name="Asset Version Published",
        description="Fires when an artist publishes a new version of an asset or shot.",
        icon="upload"
    ),
    VexsHook(
        id=2,
        name="Shot Created",
        description="Fires when a new shot is created in ShotGrid",
        icon="forward"
    ),
    VexsHook(
        id=3,
        name="Task Status Changed",
        description="Fires when the status of a task changes, for example from “In Progress” to “Final",
        icon="flag"
    ),
    VexsHook(
        id=4,
        name="Playblast Submitted",
        description="Fires when an artist submits a playblast from Maya or Houdini",
        icon="video"
    )
]


# Fetch all hook connections
def get_all_hooks() -> list[VexsHook]:
    return HOOKS

# Fetch single hook connection
def get_hook(hook_id: int) -> VexsHook | None:
    return next((h for h in HOOKS if h.id == hook_id), None)