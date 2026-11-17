from src.models.vexsHook import VexsHook

FOLDER_WATCH_HOOK_ID = 2

HOOKS: list[VexsHook] = [
    VexsHook(
        id=1,
        name="Asset Version Published",
        description="Fires when an artist publishes a new version of an asset.",
        icon="upload"
    ),
    VexsHook(
        id=FOLDER_WATCH_HOOK_ID,
        name="File Dropped in Folder",
        description="Fires when a new file is placed in the watch folder, passes graph inputs 'blend_file' (the file) and 'output_dir' (render/<file name> next to it).",
        icon="folder"
    )
]


# Fetch all hook connections
def get_all_hooks() -> list[VexsHook]:
    return HOOKS

# Fetch single hook connection
def get_hook(hook_id: int) -> VexsHook | None:
    return next((h for h in HOOKS if h.id == hook_id), None)