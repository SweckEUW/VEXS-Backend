import logging
import os
import sys
from copy import copy

# ANSI color codes per level, same colors as the uvicorn log prefix
LEVEL_COLORS = {
    logging.DEBUG: "36",  # cyan
    logging.INFO: "32",  # green
    logging.WARNING: "33",  # yellow
    logging.ERROR: "31",  # red
    logging.CRITICAL: "91",  # bright red
}
NAME_COLOR = "35"  # magenta

def _style(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"

# "INFO:     [blender_render_node] message", the logger is shortened to its module name
class ConsoleFormatter(logging.Formatter):
    def __init__(self, use_colors: bool | None = None):
        super().__init__("%(levelprefix)s [%(shortname)s] %(message)s")
        if use_colors is None:
            use_colors = sys.stderr.isatty() and "NO_COLOR" not in os.environ
        self.use_colors = use_colors

    def formatMessage(self, record: logging.LogRecord) -> str:
        level = record.levelname
        name = record.name.rsplit(".", 1)[-1]
        separator = " " * (8 - len(level))
        if self.use_colors:
            level = _style(level, LEVEL_COLORS.get(record.levelno, "0"))
            name = _style(name, NAME_COLOR)

        # Copy, so other handlers get the record without the extra fields
        record = copy(record)
        record.__dict__["levelprefix"] = f"{level}:{separator}"
        record.__dict__["shortname"] = name
        return super().formatMessage(record)

# Show INFO logs of locally evaluated nodes, uvicorn only configures its own loggers
def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(ConsoleFormatter())
    logging.basicConfig(level=level, handlers=[handler])
