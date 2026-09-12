"""Export the assembled engine. Run under `blender --background`.

    blender -b build/f110.blend -P engine/export.py -- glb
    blender -b build/f110.blend -P engine/export.py -- web     (decimated GLB)
    blender -b build/f110.blend -P engine/export.py -- stl     (one STL per part)
    blender -b build/f110.blend -P engine/export.py -- all
"""

import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")


def meshes():
    return [o for o in bpy.data.objects if o.type == "MESH"]


def deselect():
    for o in bpy.data.objects:
        o.select_set(False)


def split_sharp_edges(angle_deg=31.0):
    """Physically split the mesh at sharp edges before exporting.

    assemble.py marks sharp edges, and Blender shades them correctly -- but the
    glTF exporter does not carry the resulting split normals, so a thin-walled
    casing arrives in the browser with its outer wall's normal averaged with the
    end cap's and the inner wall's. Those faces then cull or shade black.
    Applying an Edge Split modifier bakes the split into the geometry itself, so
    correct normals survive any exporter.
    """
    n = 0
    for o in meshes():
        m = o.modifiers.new("split", "EDGE_SPLIT")
        m.split_angle = math.radians(angle_deg)
        m.use_edge_angle = True
        m.use_edge_sharp = True
        bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
            n += 1
        except RuntimeError:
            o.modifiers.remove(m)
    print(f"  edge-split applied to {n} objects")


def export_glb(name="f110.glb", draco=False):
    path = os.path.join(BUILD, name)
    deselect()
    kw = {}
    if draco:
        kw = {"export_draco_mesh_compression_enable": True,
              "export_draco_mesh_compression_level": 6}
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=False,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        **kw,
    )
    print(f"  -> {path}  ({os.path.getsize(path) / 1e6:.1f} MB)")
    return path


def export_web(target_faces=260000):
    """A decimated GLB small enough to load in a browser. Decimation is applied
    proportionally, so dense blade rows lose the most and small hardware keeps
    its shape."""
    total = sum(len(o.data.polygons) for o in meshes())
    ratio = min(1.0, target_faces / max(total, 1))
    print(f"  decimating {total:,} faces -> target {target_faces:,} (ratio {ratio:.3f})")

    for o in meshes():
        n = len(o.data.polygons)
        if n < 400:                      # leave small hardware alone
            continue
        # spend the budget where the faces actually are
        r = max(0.06, min(1.0, ratio * (1.0 + 0.35 * (1.0 - n / total))))
        m = o.modifiers.new("dec", "DECIMATE")
        m.ratio = r
        bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except RuntimeError:
            o.modifiers.remove(m)

    now = sum(len(o.data.polygons) for o in meshes())
    print(f"  decimated to {now:,} faces")
    return export_glb("f110_web.glb", draco=True)


def export_stl():
    out = os.path.join(BUILD, "stl")
    os.makedirs(out, exist_ok=True)
    n = 0
    for o in meshes():
        deselect()
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        path = os.path.join(out, o.name + ".stl")
        try:
            bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True,
                                  global_scale=1000.0)   # write in millimetres
        except AttributeError:
            bpy.ops.export_mesh.stl(filepath=path, use_selection=True,
                                    global_scale=1000.0)
        n += 1
    print(f"  -> {n} STL files in {out}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["all"]
    mode = argv[0]
    os.makedirs(BUILD, exist_ok=True)
    split_sharp_edges()
    if mode in ("glb", "all"):
        export_glb()
    if mode in ("stl", "all"):
        export_stl()
    if mode in ("web", "all"):
        export_web()
