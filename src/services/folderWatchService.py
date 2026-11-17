import logging
import os
import queue
import threading
from src.core.config import settings
from src.services import vexsHookConnectionService
from src.services.vexsHookService import FOLDER_WATCH_HOOK_ID

log = logging.getLogger(__name__)

# Size and mtime of a file, a file counts as complete once this stays the same between two polls
FileState = tuple[int, float]

_stop = threading.Event()
_jobs: queue.Queue[str] = queue.Queue()
_threads: list[threading.Thread] = []


def _extensions() -> tuple[str, ...]:
    return tuple(e.strip().lower() for e in settings.watch_folder_extensions.split(",") if e.strip())

# Files in the watch folder with a watched extension, skips hidden and temp files (.blend1 and .blend@ do not match .blend)
def _scan(folder: str) -> dict[str, FileState]:
    files: dict[str, FileState] = {}
    try:
        entries = list(os.scandir(folder))
    except OSError as exc:
        log.warning("Cannot read watch folder %s: %s", folder, exc)
        return files

    for entry in entries:
        name = entry.name
        if name.startswith((".", "~")) or not name.lower().endswith(_extensions()):
            continue
        try:
            if not entry.is_file():
                continue
            stat = entry.stat()
        except OSError:
            continue  # removed or locked while scanning
        files[entry.path] = (stat.st_size, stat.st_mtime)
    return files

# Poll the folder and queue new files once they stopped changing (copy finished)
def _watch(folder: str) -> None:
    known = set(_scan(folder))  # files already present on startup are not processed
    pending: dict[str, FileState] = {}

    while not _stop.wait(settings.watch_folder_poll_seconds):
        current = _scan(folder)
        known &= current.keys()  # a deleted file triggers again when it is dropped again

        for path, state in current.items():
            if path in known:
                continue
            if pending.get(path) == state:
                del pending[path]
                known.add(path)
                log.info("New file in watch folder: %s", path)
                _jobs.put(path)
            else:
                pending[path] = state

        for path in pending.keys() - current.keys():
            del pending[path]

# Run the connected graphs one file at a time, so renders neither overlap nor block the watcher
def _work() -> None:
    while not _stop.is_set():
        try:
            path = _jobs.get(timeout=1)
        except queue.Empty:
            continue

        # Output next to the file in render/<file name>, the watcher does not scan subfolders so it is not picked up again
        name = os.path.splitext(os.path.basename(path))[0]
        inputs = {
            "blend_file": path,
            "output_dir": os.path.join(os.path.dirname(path), "render", name),
        }

        try:
            results = vexsHookConnectionService.execute_graphs_from_vexsHook(FOLDER_WATCH_HOOK_ID, "local", inputs)
        except Exception:
            log.exception("Folder watch hook failed for %s", path)
            continue

        if not results:
            log.warning("No graph connected to hook %d, %s was not processed", FOLDER_WATCH_HOOK_ID, path)
        for result in results:
            if result.error:
                log.error("Graph '%s' (%d) failed for %s: %s", result.graph_name, result.graph_id, path, result.error)
            else:
                log.info("Graph '%s' (%d) finished for %s", result.graph_name, result.graph_id, path)


# Start watching the configured folder, does nothing without a configured folder
def start() -> None:
    if not settings.watch_folder:
        log.info("No watch folder configured, folder watch hook disabled")
        return
    if _threads:
        return

    folder = os.path.abspath(settings.watch_folder)  # normalized, so queued paths have consistent separators
    os.makedirs(folder, exist_ok=True)
    _stop.clear()
    _threads.extend([
        threading.Thread(target=_watch, args=(folder,), name="folder-watch", daemon=True),
        threading.Thread(target=_work, name="folder-watch-worker", daemon=True),
    ])
    for thread in _threads:
        thread.start()
    log.info("Watching %s for new %s files", folder, ", ".join(_extensions()))

# Stop polling, a running render is not interrupted, the daemon threads end with the process
def stop() -> None:
    _stop.set()
    _threads.clear()
