import inspect
import json
import logging
import os
import subprocess
import tempfile
import time
from typing import Any, Callable
from flowpipe import INode, InputPlug, OutputPlug
from src.flowpipeNodes.registry import register_node

log = logging.getLogger(__name__)

# Runs inside Blender, its source is written to a temp script passed via --python
def _blender_main(args: dict[str, Any]) -> None:
    import bpy, math  # pyright: ignore[reportMissingModuleSource]
    from mathutils import Vector  # pyright: ignore[reportMissingModuleSource]

    frames = args["frames"]
    scene = bpy.context.scene

    # Frame everything that renders, the scene is opened from the input .blend
    objects = list(scene.objects)
    meshes = [o for o in objects if o.type == "MESH" and not o.hide_render]
    if not meshes:
        raise RuntimeError("No renderable mesh found in scene")

    # World space bounding box of all meshes
    bpy.context.view_layer.update()
    corners = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    bb_min = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    bb_max = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    size = bb_max - bb_min
    radius = max(size.length / 2, 0.001)
    height = size.z

    # Center asset on the origin, standing on the ground
    root = bpy.data.objects.new("asset_root", None)
    scene.collection.objects.link(root)
    for obj in objects:
        if obj.parent is None:
            obj.parent = root
    root.location = (-(bb_min.x + bb_max.x) / 2, -(bb_min.y + bb_max.y) / 2, -bb_min.z)

    # Ground plane
    extent = radius * 10
    ground_mesh = bpy.data.meshes.new("ground")
    ground_mesh.from_pydata([(-extent, -extent, 0), (extent, -extent, 0), (extent, extent, 0), (-extent, extent, 0)], [], [(0, 1, 2, 3)])
    scene.collection.objects.link(bpy.data.objects.new("ground", ground_mesh))

    # Neutral world
    world = bpy.data.worlds.new("turntable_world")
    world.color = (0.05, 0.05, 0.05)
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background") if world.node_tree else None
    if background:
        background.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1.0)
    scene.world = world

    # Three point light setup, scaled to the asset
    def add_light(name: str, energy: float, location: tuple[float, float, float]) -> None:
        light = bpy.data.lights.new(name, "AREA")
        assert isinstance(light, bpy.types.AreaLight)
        light.energy = energy * radius ** 2
        light.size = radius * 2
        obj = bpy.data.objects.new(name, light)
        obj.location = location
        obj.rotation_euler = (-Vector(location) + Vector((0, 0, height / 2))).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(obj)

    add_light("key", 150, (radius * 3, -radius * 3, radius * 3))
    add_light("fill", 40, (-radius * 3, -radius * 2, radius * 1.5))
    add_light("rim", 100, (0, radius * 3, radius * 3))

    # Camera on a rotating pivot
    pivot = bpy.data.objects.new("turntable_pivot", None)
    pivot.location = (0, 0, height / 2)
    scene.collection.objects.link(pivot)

    cam_data = bpy.data.cameras.new("turntable_cam")
    cam = bpy.data.objects.new("turntable_cam", cam_data)
    scene.collection.objects.link(cam)

    # Fix the vertical FOV, framing then holds for any landscape or square resolution set at render time
    cam_data.sensor_fit = "VERTICAL"
    distance = radius / math.sin(cam_data.angle_y / 2) * 1.1
    elevation = math.radians(15)
    cam.parent = pivot
    cam.location = (0, -distance * math.cos(elevation), distance * math.sin(elevation))
    cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_data.clip_end = max(distance * 10, 100)
    scene.camera = cam

    # Full 360 degree rotation, last key one frame after the end for a seamless loop
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert("rotation_euler", index=2, frame=1)
    pivot.rotation_euler = (0, 0, 2 * math.pi)
    pivot.keyframe_insert("rotation_euler", index=2, frame=frames + 1)

    scene.frame_start = 1
    scene.frame_end = frames
    scene.render.fps = 24

    bpy.ops.wm.save_as_mainfile(filepath=args["blend_file"])


@register_node("blender.create_turntable")
class BlenderCreateTurntableNode(INode):
    # UI metadata
    category = "Blender"
    label = "Blender Create Turntable"
    description = "Builds a 360 degree turntable around the meshes of a .blend scene"
    icon = "https://api.iconify.design/mdi/rotate-360.svg?color=%23E87D0D"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        InputPlug("blend_file", self, value="")
        InputPlug("output_dir", self, value="")
        InputPlug("frames", self, value=120)
        InputPlug("blender_executable", self, value="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
        OutputPlug("blend_file", self)
        OutputPlug("frame_start", self)
        OutputPlug("frame_end", self)

    def compute(self, blend_file: str, output_dir: str, frames: int, blender_executable: str) -> dict[str, Any]:
        if not blend_file or not os.path.isfile(blend_file):
            raise ValueError(f"Blend file not found: {blend_file}")

        frames = int(frames)
        # Save next to the input .blend if no output dir is given, never overwrite the input
        output_dir = output_dir or os.path.dirname(os.path.abspath(blend_file))
        os.makedirs(output_dir, exist_ok=True)
        name = os.path.splitext(os.path.basename(blend_file))[0]
        turntable_file = os.path.join(output_dir, f"{name}_turntable.blend")

        args = {
            "blend_file": os.path.abspath(turntable_file),
            "frames": frames,
        }
        log.info("Creating turntable for '%s' (%d frames) at %s", blend_file, frames, turntable_file)
        start = time.monotonic()

        # Script file instead of --python-expr, Blender echoes the whole expr on failure and buries the traceback
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, "blender_script.py")
            with open(script, "w", encoding="utf-8") as f:
                f.write(_blender_script(_blender_main))
            _run([blender_executable, "-b", "--factory-startup", os.path.abspath(blend_file), "--python-exit-code", "1",
                  "--python", script, "--", json.dumps(args)])

        if not os.path.isfile(turntable_file):
            raise RuntimeError(f"Turntable scene missing: {turntable_file}")

        log.info("Turntable scene created in %.1fs: %s", time.monotonic() - start, turntable_file)
        return {"blend_file": turntable_file, "frame_start": 1, "frame_end": frames}


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
