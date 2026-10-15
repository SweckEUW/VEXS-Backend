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

# Printed by Blender in front of every warning, picked up from stdout and logged
WARNING_MARKER = "VEXS_WARNING"

# Runs inside Blender, its source is written to a temp script passed via --python
def _blender_main(args: dict[str, Any]) -> None:
    import bpy, importlib, os  # pyright: ignore[reportMissingModuleSource]

    asset_file = args["asset_file"]
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
        # Blender only converts UsdPreviewSurface shaders, MaterialX shading is not imported
        # pxr ships as compiled modules without usable stubs
        Usd: Any = importlib.import_module("pxr.Usd")
        UsdShade: Any = importlib.import_module("pxr.UsdShade")
        # Keep the stage referenced, prims expire while iterating a temporary stage
        stage = Usd.Stage.Open(asset_file)
        for prim in stage.Traverse():
            if not prim.IsA(UsdShade.Material):
                continue
            material = UsdShade.Material(prim)
            mtlx = material.GetSurfaceOutput("mtlx")
            preview = material.GetSurfaceOutput()
            if mtlx and mtlx.HasConnectedSource() and not (preview and preview.HasConnectedSource()):
                print(f"{args['warning_marker']} Material {prim.GetPath()} has only MaterialX shading, "
                      "no UsdPreviewSurface fallback, it will render with a default grey material", flush=True)
        bpy.ops.wm.usd_import(filepath=asset_file, import_usd_preview=True, set_material_blend=True, mtl_purpose="MTL_FULL")
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=asset_file)
    elif ext == ".blend":
        # Stub declares load() as returning None, it actually returns a context manager
        loader: Any = bpy.data.libraries.load(asset_file, link=False)
        with loader as (src, dst):
            dst.objects = src.objects
        for obj in dst.objects:
            if obj is not None:
                scene.collection.objects.link(obj)
    else:
        raise RuntimeError(f"Unsupported asset format: {ext}")

    imported = [o for o in bpy.data.objects if o not in before]
    if not any(o.type == "MESH" for o in imported):
        raise RuntimeError(f"No mesh found in asset: {asset_file}")

    # Unconverted materials (e.g. MaterialX only) come in with an empty node tree and render black
    for material in {s.material for o in imported for s in o.material_slots if s.material}:
        tree = material.node_tree
        if tree and not any(n.bl_idname == "ShaderNodeOutputMaterial" for n in tree.nodes):
            bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
            output = tree.nodes.new("ShaderNodeOutputMaterial")
            tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    bpy.ops.wm.save_as_mainfile(filepath=args["blend_file"])


@register_node("blender.load_asset")
class BlenderLoadAssetNode(INode):
    # UI metadata
    category = "Blender"
    label = "Blender Load Asset"
    description = "Imports an asset into an empty scene, saved as .blend"
    icon = "https://api.iconify.design/mdi/package-variant-closed.svg?color=%23E87D0D"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        InputPlug("asset_file", self, value="")
        InputPlug("output_dir", self, value="")
        InputPlug("blender_executable", self, value="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
        OutputPlug("blend_file", self)

    def compute(self, asset_file: str, output_dir: str, blender_executable: str) -> dict[str, Any]:
        if not asset_file or not os.path.isfile(asset_file):
            raise ValueError(f"Asset file not found: {asset_file}")
        if not output_dir:
            raise ValueError("output_dir is required")

        os.makedirs(output_dir, exist_ok=True)
        asset_name = os.path.splitext(os.path.basename(asset_file))[0]
        blend_file = os.path.join(output_dir, f"{asset_name}.blend")

        args = {
            "asset_file": os.path.abspath(asset_file),
            "blend_file": os.path.abspath(blend_file),
            "warning_marker": WARNING_MARKER,
        }
        log.info("Loading asset '%s' into %s", asset_file, blend_file)
        start = time.monotonic()

        # Script file instead of --python-expr, Blender echoes the whole expr on failure and buries the traceback
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, "blender_script.py")
            with open(script, "w", encoding="utf-8") as f:
                f.write(_blender_script(_blender_main))
            output = _run([blender_executable, "-b", "--factory-startup", "--python-exit-code", "1",
                           "--python", script, "--", json.dumps(args)])

        for line in output.splitlines():
            if line.startswith(WARNING_MARKER):
                log.warning(line[len(WARNING_MARKER):].strip())

        if not os.path.isfile(blend_file):
            raise RuntimeError(f"Asset scene missing: {blend_file}")

        log.info("Asset scene created in %.1fs: %s", time.monotonic() - start, blend_file)
        return {"blend_file": blend_file}


# Build a Blender script from a function, called with the JSON args passed after "--"
def _blender_script(func: Callable[[dict[str, Any]], None]) -> str:
    header = "import json, sys\nfrom typing import Any\n"
    call = f"{func.__name__}(json.loads(sys.argv[sys.argv.index('--') + 1]))\n"
    return header + inspect.getsource(func) + "\n" + call

# Run a process, return stdout and raise with the tail of its output on failure
def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if result.returncode != 0:
        output = (result.stdout + result.stderr)[-3000:]
        raise RuntimeError(f"{os.path.basename(cmd[0])} failed with exit code {result.returncode}:\n{output}")

    return result.stdout
