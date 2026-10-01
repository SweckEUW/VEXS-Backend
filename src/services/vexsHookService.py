from src.models.vexsHook import VexsHook

HOOKS: list[VexsHook] = [
    VexsHook(
        id=1,
        name="Asset Publish Notifier",
        description="Benachrichtigt das Team bei einem Asset-Publish",
    ),
    VexsHook(
        id=2,
        name="Shot Publish Sync",
        description="Synchronisiert Shots nach dem Publish",
    ),
    VexsHook(
        id=3,
        name="Task Complete Logger",
    ),
]


# Fetch all hook connections
def get_all_hooks() -> list[VexsHook]:
    return HOOKS

# Fetch single hook connection
def get_hook(hook_id: int) -> VexsHook | None:
    return next((h for h in HOOKS if h.id == hook_id), None)