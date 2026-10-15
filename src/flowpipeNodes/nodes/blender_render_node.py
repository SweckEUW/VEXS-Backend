import inspect
import json
import logging
import os
import subprocess
import tempfile
import threading
import time
from collections import deque
from datetime import timedelta
from typing import Any, Callable
from flowpipe import INode, InputPlug, OutputPlug
from src.flowpipeNodes.registry import register_node

log = logging.getLogger(__name__)

# Seconds between status logs while Blender renders
STATUS_INTERVAL = 10
# Printed by Blender after every rendered frame
PROGRESS_MARKER = "VEXS_FRAME_DONE"
# Printed by Blender in front of info and warning lines, picked up from stdout and logged
INFO_MARKER = "VEXS_INFO"
WARNING_MARKER = "VEXS_WARNING"

# Runs inside Blender, its source is written to a temp script passed via --python
def _blender_main(args: dict[str, Any]) -> None:
    import bpy  # pyright: ignore[reportMissingModuleSource]

    scene = bpy.context.scene
    render = scene.render
    cycles: Any = getattr(scene, "cycles")  # registered by the Cycles add-on, unknown to the stubs

    render.engine = "CYCLES"
    render.resolution_x = args["resolution_x"]
    render.resolution_y = args["resolution_y"]
    render.resolution_percentage = args["resolution_percentage"]
    # Keep BVH and shaders between frames, only the camera moves in a turntable
    render.use_persistent_data = True

    cycles.samples = args["samples"]
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = args["noise_threshold"]
    cycles.max_bounces = args["max_bounces"]

    # --factory-startup resets the preferences, so the GPU has to be enabled here
    cycles.device = "CPU"
    if args["device"] == "GPU":
        prefs: Any = bpy.context.preferences.addons["cycles"].preferences
        for backend in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
            try:
                prefs.compute_device_type = backend
            except TypeError:
                continue  # backend not available in this build
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type == backend]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == backend
                cycles.device = "GPU"
                print(f"{args['info_marker']} Rendering on {backend}: {', '.join(d.name for d in gpus)}", flush=True)
                break
        else:
            print(f"{args['warning_marker']} No GPU found, falling back to CPU", flush=True)
    if cycles.device == "CPU":
        print(f"{args['info_marker']} Rendering on CPU", flush=True)

    cycles.use_denoising = args["denoise"]
    if args["denoise"]:
        cycles.denoiser = "OPENIMAGEDENOISE"
        cycles.denoising_use_gpu = cycles.device == "GPU"

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

    # Report every finished frame, the node turns these lines into status logs
    def report_frame(*_: Any) -> None:
        print(f"{args['progress_marker']} {scene.frame_current}", flush=True)

    bpy.app.handlers.render_post.append(report_frame)
    bpy.ops.render.render(animation=True)


@register_node("blender.render")
class BlenderRenderNode(INode):
    # UI metadata
    category = "Blender"
    label = "Blender Render"
    description = "Renders a .blend file headless with Cycles to an MP4"
    icon = "https://api.iconify.design/mdi/movie-open-play.svg?color=%23E87D0D"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        InputPlug("blend_file", self, value="")
        InputPlug("frame_start", self, value=1)
        InputPlug("frame_end", self, value=120)
        InputPlug("resolution_x", self, value=1920)
        InputPlug("resolution_y", self, value=1080)
        InputPlug("resolution_percentage", self, value=100)
        InputPlug("device", self, value="GPU")
        InputPlug("samples", self, value=128)
        InputPlug("noise_threshold", self, value=0.05)
        InputPlug("denoise", self, value=True)
        InputPlug("max_bounces", self, value=6)
        InputPlug("output_dir", self, value="")
        InputPlug("blender_executable", self, value="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
        OutputPlug("mp4", self)

    def compute(self, blend_file: str, frame_start: int, frame_end: int, resolution_x: int, resolution_y: int,
                resolution_percentage: int, device: str, samples: int, noise_threshold: float, denoise: bool,
                max_bounces: int, output_dir: str, blender_executable: str) -> dict[str, Any]:
        if not blend_file or not os.path.isfile(blend_file):
            raise ValueError(f"Blend file not found: {blend_file}")

        device = (device or "GPU").upper()
        if device not in ("GPU", "CPU"):
            raise ValueError(f"Unsupported device: {device}")
        resolution_x, resolution_y = int(resolution_x), int(resolution_y)
        if resolution_x < 1 or resolution_y < 1:
            raise ValueError(f"Invalid resolution: {resolution_x}x{resolution_y}")
        resolution_percentage = int(resolution_percentage)
        if not 1 <= resolution_percentage <= 100:
            raise ValueError(f"resolution_percentage must be between 1 and 100: {resolution_percentage}")
        samples = int(samples)
        if samples < 1:
            raise ValueError(f"samples must be at least 1: {samples}")
        noise_threshold = float(noise_threshold)
        if noise_threshold <= 0:
            raise ValueError(f"noise_threshold must be greater than 0: {noise_threshold}")
        max_bounces = int(max_bounces)
        if max_bounces < 0:
            raise ValueError(f"max_bounces must not be negative: {max_bounces}")

        # Render next to the .blend if no output dir is given
        output_dir = output_dir or os.path.dirname(os.path.abspath(blend_file))
        os.makedirs(output_dir, exist_ok=True)
        name = os.path.splitext(os.path.basename(blend_file))[0]
        mp4 = os.path.join(output_dir, f"{name}.mp4")
        frame_start, frame_end = int(frame_start), int(frame_end)

        args = {
            "mp4": os.path.abspath(mp4),
            "frame_start": frame_start,
            "frame_end": frame_end,
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "resolution_percentage": resolution_percentage,
            "device": device,
            "samples": samples,
            "noise_threshold": noise_threshold,
            "denoise": bool(denoise),
            "max_bounces": max_bounces,
            "progress_marker": PROGRESS_MARKER,
            "info_marker": INFO_MARKER,
            "warning_marker": WARNING_MARKER,
        }
        log.info("Rendering '%s' frames %d-%d at %dx%d (%d%%), %d samples on %s to %s", blend_file, frame_start, frame_end,
                 resolution_x, resolution_y, resolution_percentage, samples, device, mp4)
        start = time.monotonic()

        # Script file instead of --python-expr, Blender echoes the whole expr on failure and buries the traceback
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, "blender_script.py")
            with open(script, "w", encoding="utf-8") as f:
                f.write(_blender_script(_blender_main))
            _run([blender_executable, "-b", "--factory-startup", os.path.abspath(blend_file), "--python-exit-code", "1",
                  "--python", script, "--", json.dumps(args)], name, frame_end - frame_start + 1)

        if not os.path.isfile(mp4):
            raise RuntimeError(f"Render output missing: {mp4}")

        log.info("Render of '%s' finished in %s: %s", name, _duration(time.monotonic() - start), mp4)
        return {"mp4": mp4}


# Build a Blender script from a function, called with the JSON args passed after "--"
def _blender_script(func: Callable[[dict[str, Any]], None]) -> str:
    header = "import json, sys\nfrom typing import Any\n"
    call = f"{func.__name__}(json.loads(sys.argv[sys.argv.index('--') + 1]))\n"
    return header + inspect.getsource(func) + "\n" + call

# Run Blender, log its progress every STATUS_INTERVAL seconds and raise with the tail of its output on failure
def _run(cmd: list[str], name: str, total_frames: int) -> None:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    tail: deque[str] = deque(maxlen=200)
    frames_done = 0

    # Read in a thread, so status logs keep coming while Blender prints nothing (scene loading, shader compilation)
    def read_output() -> None:
        nonlocal frames_done
        assert process.stdout is not None
        for line in process.stdout:
            if line.startswith(PROGRESS_MARKER):
                frames_done += 1
            elif line.startswith(INFO_MARKER):
                log.info("Rendering '%s': %s", name, line[len(INFO_MARKER):].strip())
            elif line.startswith(WARNING_MARKER):
                log.warning("Rendering '%s': %s", name, line[len(WARNING_MARKER):].strip())
            else:
                tail.append(line)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    start = time.monotonic()
    try:
        while True:
            try:
                process.wait(timeout=STATUS_INTERVAL)
                break
            except subprocess.TimeoutExpired:
                _log_status(name, frames_done, total_frames, time.monotonic() - start)
    except BaseException:
        # Don't leave Blender running if the node is interrupted
        process.kill()
        raise
    reader.join()

    if process.returncode != 0:
        output = "".join(tail)[-3000:]
        raise RuntimeError(f"{os.path.basename(cmd[0])} failed with exit code {process.returncode}:\n{output}")

def _log_status(name: str, done: int, total: int, elapsed: float) -> None:
    if not done:
        log.info("Rendering '%s': waiting for first frame, elapsed %s", name, _duration(elapsed))
        return

    remaining = elapsed / done * (total - done)
    log.info("Rendering '%s': %d/%d frames (%d%%), elapsed %s, remaining ~%s",
             name, done, total, done * 100 // total, _duration(elapsed), _duration(remaining))

# Format seconds as h:mm:ss
def _duration(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))
