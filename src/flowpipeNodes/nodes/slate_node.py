import json
import logging
import os
import subprocess
from datetime import date
from typing import Any
from flowpipe import INode, InputPlug, OutputPlug
from src.flowpipeNodes.registry import register_node

log = logging.getLogger(__name__)

@register_node("media.slate")
class SlateNode(INode):
    # UI metadata
    category = "Media"
    label = "Slate"
    description = "Prepends a slate with project, asset, artist, date and version to an MP4"
    icon = "https://api.iconify.design/mdi/movie-open.svg?color=%23A78BFA"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        InputPlug("mp4", self, value="")
        InputPlug("project", self, value="")
        InputPlug("asset_name", self, value="")
        InputPlug("artist", self, value="")
        InputPlug("version", self, value=1)
        InputPlug("slate_frames", self, value=24)
        InputPlug("ffmpeg_executable", self, value="ffmpeg")
        InputPlug("font_file", self, value="C:/Windows/Fonts/arial.ttf")
        OutputPlug("slated_mp4", self)

    def compute(self, mp4: str, project: str, asset_name: str, artist: str, version: int, slate_frames: int, ffmpeg_executable: str, font_file: str) -> dict[str, Any]:
        if not mp4 or not os.path.isfile(mp4):
            raise ValueError(f"Input video not found: {mp4}")
        if not font_file or not os.path.isfile(font_file):
            raise ValueError(f"Font file not found: {font_file}")

        # Never overwrite the input, write a new file next to it
        stem, _ = os.path.splitext(mp4)
        slated_mp4 = f"{stem}_slate.mp4"

        width, height, fps = _probe_video(ffmpeg_executable, mp4)
        log.info("Adding %d slate frames to '%s' (%dx%d @ %s fps)", int(slate_frames), mp4, width, height, fps)

        lines = [
            ("project", project),
            ("asset", asset_name),
            ("artist", artist),
            ("date", date.today().isoformat()),
            ("version", f"v{int(version):03d}"),
        ]
        font = _escape(font_file.replace("\\", "/"))
        font_size = max(height // 20, 12)

        # Black slate frames, label and value column per line
        slate = f"color=c=black:s={width}x{height}:r={fps},trim=end_frame={int(slate_frames)},format=yuv420p,setsar=1"
        for i, (key, value) in enumerate(lines):
            y = f"(h-{len(lines)}*{font_size}*1.6)/2+{i}*{font_size}*1.6"
            for x, text, color in (("w*0.1", key.upper(), "gray"), ("w*0.3", value, "white")):
                slate += (f",drawtext=fontfile='{font}':text='{_escape(text)}':expansion=none"
                          f":fontcolor={color}:fontsize={font_size}:x={x}:y={y}")

        filter_graph = f"{slate}[slate];[0:v]format=yuv420p,setsar=1[main];[slate][main]concat=n=2:v=1:a=0[out]"

        _run([ffmpeg_executable, "-y", "-v", "error", "-i", mp4, "-filter_complex", filter_graph,
              "-map", "[out]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-an", slated_mp4])

        if not os.path.isfile(slated_mp4):
            raise RuntimeError(f"Slated video missing: {slated_mp4}")

        log.info("Slated video written: %s", slated_mp4)
        return {"slated_mp4": slated_mp4}


# Read width, height and frame rate of the first video stream via ffprobe (next to ffmpeg)
def _probe_video(ffmpeg_executable: str, path: str) -> tuple[int, int, str]:
    directory, name = os.path.split(ffmpeg_executable)
    ffprobe = os.path.join(directory, name.replace("ffmpeg", "ffprobe"))

    output = _run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
                   "stream=width,height,r_frame_rate", "-of", "json", path])
    streams = json.loads(output).get("streams", [])
    if not streams:
        raise RuntimeError(f"No video stream found: {path}")

    stream = streams[0]
    return int(stream["width"]), int(stream["height"]), stream["r_frame_rate"]

# Escape a value for use inside a quoted drawtext option
def _escape(value: str) -> str:
    return str(value).replace("\\", "").replace("'", "\u2019").replace(":", "\\:")

# Run a process, return stdout and raise with the tail of its output on failure
def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if result.returncode != 0:
        output = (result.stdout + result.stderr)[-3000:]
        raise RuntimeError(f"{os.path.basename(cmd[0])} failed with exit code {result.returncode}:\n{output}")

    return result.stdout
