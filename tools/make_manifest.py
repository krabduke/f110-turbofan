"""Generate viewer/parts.json from build/parts.csv and engine/spec.py."""
import csv, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import spec  # noqa: E402

MODULES = [
    ("01 Inlet and Fan",       "Inlet & fan",      "#7C99A5", "gas"),
    ("02 HP Compressor",       "HP compressor",    "#8D96A0", "gas"),
    ("03 Combustor",           "Combustor",        "#B4623B", "gas"),
    ("04 Turbines",            "Turbines",         "#A6512C", "gas"),
    ("05 Augmentor",           "Augmentor",        "#BE6B3E", "gas"),
    ("06 Nozzle",              "Nozzle",           "#8E6A55", "gas"),
    ("07 Casings and Frames",  "Casings & frames", "#6C7573", "struct"),
    ("08 Shafts and Bearings", "Shafts & bearings","#7D7E78", "struct"),
    ("09 Accessories",         "Accessories",      "#727868", "struct"),
]


def flowpath():
    """Gas-path centre-lines for the airflow visualisation.

    Each entry is (station mm, inner radius, outer radius) -- the real annulus
    the air actually passes through, taken from the same numbers the geometry
    is built from. Temperatures are total temperature in degrees C at max power.
    """
    S, B, C, N = spec.STATION, spec.BYPASS, spec.COMBUSTOR, spec.NOZZLE
    hpc0, hpc9 = spec.HPC_ROWS[0], spec.HPC_ROWS[-1]
    hpt, lpt = spec.HPT_ROWS[1], spec.LPT_ROWS[-1]

    core = [
        (S["inlet_lip"],      95.0,  590.0),
        (S["fan_face"],      236.0,  590.0),
        (S["fan_exit"],      340.0,  575.0),
        (S["splitter"],      344.0,  B["splitter_radius"]),
        (hpc0.x,             hpc0.r_hub_le, hpc0.r_tip_le),
        (hpc9.x,             hpc9.r_hub_te, hpc9.r_tip_te),
        (C["x_front"],       C["liner_inner_r"], C["liner_outer_r"]),
        (C["x_exit"],        314.0,  396.0),
        (hpt.x,              hpt.r_hub_le, hpt.r_tip_le),
        (lpt.x,              lpt.r_hub_te, lpt.r_tip_te),
        (S["mixer_front"],   300.0,  428.0),
        (S["mixer_exit"],     70.0,  404.0),
        (S["augmentor_exit"], 40.0,  404.0),
        (N["x_throat"],       22.0,  N["r_throat"]),
        (N["x_exit"],         14.0,  N["r_exit"]),
    ]
    bypass = [
        (S["splitter"],     B["splitter_radius"], 575.0),
        (S["fan_frame"],    B["inner_radius_fwd"], B["outer_radius_fwd"]),
        (S["mixer_front"],  B["inner_radius_aft"], B["outer_radius_aft"]),
        (S["mixer_exit"],   360.0, 428.0),
    ]
    # (station, temperature C). Dry and augmented differ only aft of the mixer.
    core_t_dry = [(S["inlet_lip"], 15), (S["fan_exit"], 95), (S["hpc_exit"], 500),
                  (C["x_exit"], 1400), (S["hpt_exit"], 1150), (S["lpt_exit"], 800),
                  (S["mixer_exit"], 700), (N["x_exit"], 640)]
    core_t_ab = [(S["inlet_lip"], 15), (S["fan_exit"], 95), (S["hpc_exit"], 500),
                 (C["x_exit"], 1400), (S["hpt_exit"], 1150), (S["lpt_exit"], 800),
                 (S["mixer_exit"], 760), (S["flameholder"], 1200),
                 (S["augmentor_exit"], 1750), (N["x_exit"], 1690)]
    bypass_t = [(S["splitter"], 95), (S["mixer_exit"], 95)]

    return {"core": core, "bypass": bypass, "core_t_dry": core_t_dry,
            "core_t_ab": core_t_ab, "bypass_t": bypass_t}


def main():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "build", "parts.csv"))))
    mods = []
    for key, label, color, kind in MODULES:
        mine = [r for r in rows if r["collection"] == key]
        if not mine:
            continue
        mods.append({
            "key": key, "label": label, "color": color, "kind": kind,
            "x0": min(float(r["x_min_mm"]) for r in mine),
            "x1": max(float(r["x_max_mm"]) for r in mine),
            "parts": len(mine),
            "faces": sum(int(r["faces"]) for r in mine),
        })
    parts = {r["name"]: {
        "m": r["collection"], "mat": r["material"],
        "x0": float(r["x_min_mm"]), "x1": float(r["x_max_mm"]),
        "f": int(r["faces"]), "n": r["count"] or None,
        # which spool this part turns with, and which way. The viewer used to
        # hold this as two regular expressions in its HTML, where a renamed
        # rotor stopped turning silently and nothing could test it.
        "spool": r.get("spool") or None,
        "spin": float(r["spin"]) if r.get("spin") else None,
    } for r in rows}

    out = {
        "engine": spec.ENGINE_NAME,
        "length": spec.LENGTH, "diameter": spec.MAX_DIAMETER,
        "weight": spec.DRY_WEIGHT_KG,
        "bpr": spec.BYPASS_RATIO, "opr": spec.OVERALL_PRESSURE_RATIO,
        "thrust_dry": spec.THRUST_DRY_N, "thrust_ab": spec.THRUST_AB_N,
        "airfoils": spec.total_airfoil_count(),
        "rows": len(spec.all_blade_rows()),
        "x_front": spec.STATION["inlet_lip"], "x_rear": spec.STATION["nozzle_exit"],
        "stations": dict(spec.STATION),
        "palette": {k: {"rgb": list(v[0]), "metal": v[1], "rough": v[2]}
                    for k, v in spec.PALETTE.items()},
        "flow": flowpath(),
        "modules": mods, "parts": parts,
    }
    path = os.path.join(ROOT, "viewer", "parts.json")
    json.dump(out, open(path, "w"), indent=1)
    print(f"  -> {path}  ({len(parts)} parts, {len(mods)} modules)")


if __name__ == "__main__":
    main()
