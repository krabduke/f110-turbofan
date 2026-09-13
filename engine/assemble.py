"""Build the complete engine in Blender. Run under `blender --background`.

Pipeline per object:
    pure-Python (verts, faces) in mm
      -> scaled to metres and made into a bpy mesh
      -> boolean cutters applied  (cooling holes, dilution holes, screech holes)
      -> rotational array applied (cooled blade prototypes -> full row)
      -> material assigned by name, filed into a collection, shaded smooth

Writes build/parts.csv so the result can be checked against spec.py by
measurement rather than by eye.
"""

import csv
import math
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import spec              # noqa: E402
import mesh as meshlib   # noqa: E402
import materials         # noqa: E402
from parts import (rotating, statics, combustor,       # noqa: E402
                   turbine, augmentor, nozzle, accessories)

MM = 0.001   # engine geometry is authored in mm; Blender scene is metres

MODULES = [
    ("rotating", rotating),
    ("statics", statics),
    ("combustor", combustor),
    ("turbine", turbine),
    ("augmentor", augmentor),
    ("nozzle", nozzle),
    ("accessories", accessories),
]

COLLECTIONS = [
    "01 Inlet and Fan", "02 HP Compressor", "03 Combustor", "04 Turbines",
    "05 Augmentor", "06 Nozzle", "07 Casings and Frames",
    "08 Shafts and Bearings", "09 Accessories",
]


def collection_for(name):
    n = name.lower()
    if n.startswith("shaft") or n.startswith("brg"):
        return "08 Shafts and Bearings"
    if any(k in n for k in ("gearbox", "towershaft", "fuel_line",
                            "oil_line", "harness", "mount")):
        return "09 Accessories"
    if any(k in n for k in ("casing", "flange", "frame", "inlet",
                            "bypass", "splitter", "strut")):
        return "07 Casings and Frames"
    if "nozzle_" in n:
        return "06 Nozzle"
    if any(k in n for k in ("mixer", "flameholder", "spraybar", "augmentor")):
        return "05 Augmentor"
    if any(k in n for k in ("hpt", "lpt", "turbine")):
        return "04 Turbines"
    if any(k in n for k in ("combustor", "fuel_nozzle", "fuel_manifold",
                            "igniter", "diffuser", "swirler", "dome")):
        return "03 Combustor"
    if "hpc" in n:
        return "02 HP Compressor"
    return "01 Inlet and Fan"


def material_for(name):
    """Longest matching key in MATERIAL_MAP wins, so 'towershaft' beats 'shaft'."""
    n = name.lower()
    best, best_len = spec.DEFAULT_MATERIAL, -1
    for key, mat in spec.MATERIAL_MAP.items():
        if key in n and len(key) > best_len:
            best, best_len = mat, len(key)
    return best


# --------------------------------------------------------------------------

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"


def make_object(name, verts, faces, collection=None, scale=MM):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x * scale, y * scale, z * scale) for (x, y, z) in verts],
                   [], [list(f) for f in faces])
    me.validate(verbose=False)
    me.update()
    obj = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def apply_cutters(obj, cut_verts, cut_faces):
    """Boolean-difference a joined cutter mesh out of obj, then bin the cutter."""
    cutter = make_object(obj.name + "__cutter", cut_verts, cut_faces,
                         bpy.context.scene.collection)
    m = obj.modifiers.new("holes", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    m.object = cutter
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=m.name)
        ok = True
    except RuntimeError as exc:
        print(f"    ! boolean failed on {obj.name}: {exc}")
        obj.modifiers.remove(m)
        ok = False
    bpy.data.objects.remove(cutter, do_unlink=True)
    return ok


def array_rotational(obj, count):
    """Replicate the object's own mesh `count` times about +X, in place.
    Done after the boolean so per-blade detail is cut exactly once."""
    verts = [tuple(v.co) for v in obj.data.vertices]
    faces = [tuple(p.vertices) for p in obj.data.polygons]
    nv, nf = meshlib.replicate(verts, faces, count)
    me = bpy.data.meshes.new(obj.name + "_arr")
    me.from_pydata(nv, [], [list(f) for f in nf])
    me.validate(verbose=False)
    me.update()
    old = obj.data
    obj.data = me
    bpy.data.meshes.remove(old)


def recalc_normals(obj):
    """Make normals point outward, resolved by Blender from the winding.

    Without this the revolved casings arrive with normals that shade most of
    the hull black -- the geometry is complete (an unlit material renders a
    full silhouette), but the shading normals are wrong. The sibling aircraft
    and car projects both do this and neither shows the artefact.
    """
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def shade_smooth(obj, angle_deg=32.0):
    """Smooth around the revolution, sharp across profile corners.

    bpy.ops.object.shade_smooth_by_angle can fail silently in background mode,
    which leaves every polygon smooth. On a thin-walled tube that averages the
    outer wall's normal with the end cap's and the inner wall's, and the result
    points inward -- the surface then samples the environment from the wrong
    hemisphere and renders black. Marking sharp edges directly is deterministic.
    """
    me = obj.data
    for p in me.polygons:
        p.use_smooth = True

    limit = math.cos(math.radians(angle_deg))
    normals = [tuple(p.normal) for p in me.polygons]
    faces_of_edge = {}
    for pi, poly in enumerate(me.polygons):
        for ek in poly.edge_keys:
            faces_of_edge.setdefault(ek, []).append(pi)

    edge_by_key = {e.key: e for e in me.edges}
    n_sharp = 0
    for ek, faces in faces_of_edge.items():
        edge = edge_by_key.get(ek)
        if edge is None:
            continue
        if len(faces) != 2:
            edge.use_edge_sharp = True      # boundary or non-manifold
            n_sharp += 1
            continue
        a, b = normals[faces[0]], normals[faces[1]]
        if sum(x * y for x, y in zip(a, b)) < limit:
            edge.use_edge_sharp = True
            n_sharp += 1
    return n_sharp


# --------------------------------------------------------------------------

def main():
    t0 = time.time()
    clear_scene()
    mats = materials.build_all()

    cols = {}
    for cname in COLLECTIONS:
        c = bpy.data.collections.new(cname)
        bpy.context.scene.collection.children.link(c)
        cols[cname] = c

    rows = []
    n_bool = n_bool_ok = n_sharp = 0

    for modname, module in MODULES:
        t1 = time.time()
        built = module.build()
        arrays = getattr(module, "ARRAYS", {})
        objects = {k: v for k, v in built.items() if not k.startswith("cut:")}
        cutters = {k[4:]: v for k, v in built.items() if k.startswith("cut:")}

        for name, (verts, faces) in sorted(objects.items()):
            cname = collection_for(name)
            obj = make_object(name, verts, faces, cols[cname])

            if name in cutters:
                n_bool += 1
                if apply_cutters(obj, *cutters[name]):
                    n_bool_ok += 1
            if name in arrays:
                array_rotational(obj, arrays[name])

            recalc_normals(obj)
            mat_name = material_for(name)
            obj.data.materials.append(mats[mat_name])
            n_sharp += shade_smooth(obj)

            bb = meshlib.bbox([tuple(v.co) for v in obj.data.vertices])
            rows.append({
                "name": name,
                "collection": cname,
                "material": mat_name,
                "verts": len(obj.data.vertices),
                "faces": len(obj.data.polygons),
                "x_min_mm": round(bb[0] / MM, 1), "x_max_mm": round(bb[3] / MM, 1),
                "y_min_mm": round(bb[1] / MM, 1), "y_max_mm": round(bb[4] / MM, 1),
                "z_min_mm": round(bb[2] / MM, 1), "z_max_mm": round(bb[5] / MM, 1),
                "count": arrays.get(name, ""),
            })
        print(f"  [{modname}] {len(objects)} objects in {time.time() - t1:.1f}s")

    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    csv_path = os.path.join(ROOT, "build", "parts.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    tv = sum(r["verts"] for r in rows)
    tf = sum(r["faces"] for r in rows)
    print(f"\n{len(rows)} objects | {tv:,} verts | {tf:,} faces")
    print(f"booleans: {n_bool_ok}/{n_bool} applied")
    print(f"sharp edges marked: {n_sharp:,}")
    print(f"parts.csv -> {csv_path}")

    blend = os.path.join(ROOT, "build", "f110.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print(f"blend     -> {blend}")
    print(f"total {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
