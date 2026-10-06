import inspect
import json
import os
import subprocess
from typing import Any, Callable
from flowpipe import INode, InputPlug, OutputPlug
from src.flowpipeNodes.registry import register_node

# Runs inside Blender, its source is passed to Blender via --python-expr
def _blender_main(args: dict[str, Any]) -> None:
    import bpy, math, os
    from mathutils import Vector

    asset_file = args["asset_file"]
    frames = args["frames"]
    scene = bpy.context.scene

    # Start from an empty scene
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    # Import asset depending on file extension
    before = set(bpy.data.objects)
    ext = os.path.splitext(asset_file)[1].lower()
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=asset_file)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=asset_file)
    elif ext == ".abc":
        bpy.ops.wm.alembic_import(filepath=asset_file)
    elif ext in (".usd", ".usda", ".usdc", ".usdz"):
        bpy.ops.wm.usd_import(filepath=asset_file)
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=asset_file)
    elif ext == ".blend":
        with bpy.data.libraries.load(asset_file, link=False) as (src, dst):
            dst.objects = src.objects
        for obj in dst.objects:
            if obj is not None:
                scene.collection.objects.link(obj)
    else:
        raise RuntimeError(f"Unsupported asset format: {ext}")

    imported = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in imported if o.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh found in asset: {asset_file}")

    # World space bounding box of all imported meshes
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
    for obj in imported:
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
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1.0)
    scene.world = world

    # Three point light setup, scaled to the asset
    def add_light(name, energy, location):
        light = bpy.data.lights.new(name, "AREA")
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

    res_x, res_y = args["resolution_x"], args["resolution_y"]
    fov_h = cam_data.angle
    fov_v = 2 * math.atan(math.tan(fov_h / 2) * res_y / res_x)
    distance = radius / math.sin(min(fov_h, fov_v) / 2) * 1.1
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
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100

    bpy.ops.wm.save_as_mainfile(filepath=args["blend_file"])


@register_node("blender.create_turntable")
class BlenderCreateTurntableNode(INode):
    # UI metadata
    category = "Blender"
    label = "Blender Create Turntable"
    description = "Imports an asset and builds a 360 degree turntable scene, saved as .blend"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        InputPlug("asset_file", self, value="")
        InputPlug("output_dir", self, value="")
        InputPlug("frames", self, value=120)
        InputPlug("resolution_x", self, value=1920)
        InputPlug("resolution_y", self, value=1080)
        InputPlug("blender_executable", self, value="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
        OutputPlug("blend_file", self)
        OutputPlug("frame_start", self)
        OutputPlug("frame_end", self)

    def compute(self, asset_file: str, output_dir: str, frames: int, resolution_x: int, resolution_y: int, blender_executable: str) -> dict:
        if not asset_file or not os.path.isfile(asset_file):
            raise ValueError(f"Asset file not found: {asset_file}")
        if not output_dir:
            raise ValueError("output_dir is required")

        frames = int(frames)
        os.makedirs(output_dir, exist_ok=True)
        asset_name = os.path.splitext(os.path.basename(asset_file))[0]
        blend_file = os.path.join(output_dir, f"{asset_name}_turntable.blend")

        args = {
            "asset_file": os.path.abspath(asset_file),
            "blend_file": os.path.abspath(blend_file),
            "frames": frames,
            "resolution_x": int(resolution_x),
            "resolution_y": int(resolution_y),
        }
        _run([blender_executable, "-b", "--factory-startup", "--python-exit-code", "1",
              "--python-expr", _blender_script(_blender_main), "--", json.dumps(args)])

        if not os.path.isfile(blend_file):
            raise RuntimeError(f"Turntable scene missing: {blend_file}")

        return {"blend_file": blend_file, "frame_start": 1, "frame_end": frames}


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
