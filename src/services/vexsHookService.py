from src.models.vexsHook import Hook, HookType

HOOKS: list[Hook] = [
    Hook(
        id=1,
        name="Asset Publish Notifier",
        description="Benachrichtigt das Team bei einem Asset-Publish",
        type=HookType.ON_ASSET_PUBLISH,
    ),
    Hook(
        id=2,
        name="Shot Publish Sync",
        description="Synchronisiert Shots nach dem Publish",
        type=HookType.ON_SHOT_PUBLISH,
    ),
    Hook(
        id=3,
        name="Task Complete Logger",
        type=HookType.ON_TASK_COMPLETE,
    ),
]


# Fetch all hook connections
def get_all_hooks() -> list[Hook]:
    return HOOKS

# Fetch single hook connection
def get_hook(hook_id: int) -> Hook | None:
    return next((h for h in HOOKS if h.id == hook_id), None)