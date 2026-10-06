import inspect
import json
import os
import subprocess
from typing import Any, Callable
from flowpipe import INode, InputPlug, OutputPlug
from src.flowpipeNodes.registry import register_node

# Runs inside Blender, its source is passed to Blender via --python-expr
def _blender_main(args: dict[str, Any]) -> None:
    import bpy

    scene = bpy.context.scene
    render = scene.render

    # Map engine names to the identifiers known by this Blender version
    engines = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
    if args["engine"] == "CYCLES":
        render.engine = "CYCLES"
    elif "BLENDER_EEVEE_NEXT" in engines:
        render.engine = "BLENDER_EEVEE_NEXT"
    else:
        render.engine = "BLENDER_EEVEE"

    scene.frame_start = args["frame_start"]
    scene.frame_end = args["frame_end"]

    # Direct H.264 MP4 output (Blender 5 introduced media_type)
    image_settings = render.image_settings
    if hasattr(image_settings, "media_type"):
        image_settings.media_type = "VIDEO"
    image_settings.file_format = "FFMPEG"
    render.ffmpeg.format = "MPEG4"
    render.ffmpeg.codec = "H264"
    render.ffmpeg.constant_rate_factor = "HIGH"
    render.ffmpeg.audio_codec = "NONE"
    render.use_file_extension = False
    render.filepath = args["mp4"]

    bpy.ops.render.render(animation=True)


@register_node("blender.render")
class BlenderRenderNode(INode):
    # UI metadata
    category = "Blender"
    label = "Blender Render"
    description = "Renders a .blend file headless to an MP4"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        InputPlug("blend_file", self, value="")
        InputPlug("frame_start", self, value=1)
        InputPlug("frame_end", self, value=120)
        InputPlug("engine", self, value="EEVEE")
        InputPlug("output_dir", self, value="")
        InputPlug("blender_executable", self, value="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
        OutputPlug("mp4", self)

    def compute(self, blend_file: str, frame_start: int, frame_end: int, engine: str, output_dir: str, blender_executable: str) -> dict:
        if not blend_file or not os.path.isfile(blend_file):
            raise ValueError(f"Blend file not found: {blend_file}")

        engine = (engine or "EEVEE").upper()
        if engine not in ("EEVEE", "CYCLES"):
            raise ValueError(f"Unsupported engine: {engine}")

        # Render next to the .blend if no output dir is given
        output_dir = output_dir or os.path.dirname(os.path.abspath(blend_file))
        os.makedirs(output_dir, exist_ok=True)
        name = os.path.splitext(os.path.basename(blend_file))[0]
        mp4 = os.path.join(output_dir, f"{name}.mp4")

        args = {
            "mp4": os.path.abspath(mp4),
            "frame_start": int(frame_start),
            "frame_end": int(frame_end),
            "engine": engine,
        }
        _run([blender_executable, "-b", "--factory-startup", os.path.abspath(blend_file), "--python-exit-code", "1",
              "--python-expr", _blender_script(_blender_main), "--", json.dumps(args)])

        if not os.path.isfile(mp4):
            raise RuntimeError(f"Render output missing: {mp4}")

        return {"mp4": mp4}


# Build a Blender script from a function, called with the JSON args passed after "--"
def _blender_script(func: Callable[[dict[str, Any]], None]) -> str:
    header = "import json, sys\nfrom typing import Any\n"
    call = f"{func.__name__}(json.loads(sys.argv[sys.argv.index('--') + 1]))\n"
    return header + inspect.getsource(func) + "\n" + call

# Run a process and raise with the tail of its output on failure
def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if result.returncode != 0:
        output = (result.stdout + result.stderr)[-3000:]
        raise RuntimeError(f"{os.path.basename(cmd[0])} failed with exit code {result.returncode}:\n{output}")
