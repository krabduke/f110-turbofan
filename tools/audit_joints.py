"""Does the engine hold together, and is the gas path continuous?

    python3 tools/audit_joints.py

Every other audit here is one-sided. `audit_intersect` lists parts sharing
material and `audit_clearance` lists parts that got too close -- both are looking for
things that touch when they should not. A bleed pipe that stops 40 mm short of the casing boss it leaves passes both, because not
touching is exactly what they want to see.

That is the defect this catches, and it is the commonest one in a model built
a part at a time: something moves, the thing that lands on it does not, and
the only witness is a render from the one angle where the joint is not hidden
behind something else.

`audit_intersect.EXPECTED` is nearly this list already -- naming two parts
there says they are meant to be one assembly -- but it is a permission, not a
requirement. Nothing there fails when one of them drifts away; the entry just
stops applying. The circuits below are the same knowledge stated as an
obligation.

Three checks:

  ASSEMBLY   every part is attached to the machine, however indirectly
  CIRCUITS   each declared run of material is continuous, link by link
  MODULES    no two modules build a part under the same name, and no cutter
             is aimed at a part its own module does not build

CONTACT is 2 mm. Parts that are bolted, welded or bonded together in
this model interpenetrate, so anything further apart than that is not a joint.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _joints  # noqa: E402

CONTACT_MM = 2.0
ROOT_PART = 'casing_fan'
PKG = 'engine/parts'
UNIT = 'mm'

CIRCUITS = [
    ("the case is one pressure vessel, front to back",
     ["inlet_lip", "casing_inlet", "casing_fan", "casing_bypass",
      "casing_turbine", "casing_augmentor"]),
    ("and it is flanged at every joint",
     ["casing_inlet", "flange_inlet", "casing_fan"]),
    ("the core case hangs inside the bypass duct",
     ["splitter", "bypass_inner_wall", "casing_combustor", "casing_turbine"]),
    ("the fan frame carries the front bearings out to the case",
     ["fan_frame_hub", "fan_frame_struts", "bypass_struts", "casing_bypass"]),
    ("the turbine frame carries the rear bearing into the case",
     ["casing_turbine", "turbine_frame_struts", "turbine_frame_hub"]),
    ("core gas path: fan to splitter to compressor",
     ["vanes_fan_ogv", "bypass_struts", "splitter", "fan_frame_struts",
      "casing_hpc"]),
    ("compressor to diffuser to combustor",
     ["vanes_hpc_s9", "diffuser", "combustor_dome"]),
    ("and the diffuser carries both liners",
     ["diffuser", "combustor_liner_outer", "igniters"]),
    ("combustor to turbine",
     ["combustor_liner_inner", "blades_hpt_ngv", "blades_hpt_r1",
      "hpt_disc"]),
    # through the static structure: the LP turbine's disc turns inside the
    # frame and must not touch it, so the path runs case, frame, mixer
    ("turbine to mixer to augmentor",
     ["casing_turbine", "turbine_frame_struts", "mixer", "augmentor_liner"]),
    ("the nozzle hangs off the augmentor case",
     ["casing_augmentor", "nozzle_flaps_convergent", "nozzle_flaps_divergent",
      "nozzle_ext_flaps"]),
    ("and is actuated",
     ["casing_augmentor", "nozzle_actuators", "nozzle_actuator_ring",
      "nozzle_links", "nozzle_ext_flaps"]),
    ("the low spool is one rotating assembly",
     ["fan_disc_assembly", "shaft_lp", "lpt_disc_assembly"]),
    ("the high spool is one rotating assembly",
     ["hpc_drum", "hpc_rear_cone", "shaft_hp", "hpt_disc"]),
    ("fan blades are in the fan disc",
     ["fan_disc_assembly", "blades_fan_r1"]),
    ("compressor blades are on the drum",
     ["hpc_drum", "blades_hpc_r1"]),
    ("compressor stators are in the case",
     ["casing_hpc", "vanes_hpc_s1"]),
    ("the variable vanes are driven",
     ["variable_vane_actuation", "casing_hpc"]),
    ("the low spool runs on its bearings",
     ["shaft_lp", "brg_1_lp_thrust", "bearing_sumps"]),
    ("the high spool runs on its bearings",
     ["shaft_hp", "brg_3_hp_thrust"]),
    ("fuel: lines to manifold to nozzles into the dome",
     ["fuel_lines", "fuel_manifold", "fuel_nozzles", "combustor_dome"]),
    ("ignition: exciter to lead to igniter",
     ["ignition_exciters", "igniters"]),
    ("the augmentor is fuelled",
     ["spraybars", "augmentor_liner"]),
    ("and flame-held",
     ["flameholder", "augmentor_liner"]),
    ("the accessory gearbox is driven off the high spool",
     ["shaft_hp", "towershaft", "gearbox"]),
    ("and it drives the accessories",
     ["gearbox", "generator_1"]),
    ("the gearbox is mounted to the case",
     ["gearbox", "gearbox_mounts", "casing_fan"]),
    ("oil: tank to pump to the sumps",
     ["oil_tank", "oil_lines", "oil_pressure_pump"]),
    ("and the lines reach the bearings, through the frame that carries them",
     ["oil_lines", "casing_turbine", "turbine_frame_struts",
      "turbine_frame_hub", "bearing_sumps"]),
    ("scavenge returns through the gearbox",
     ["oil_lines", "oil_scavenge_pump", "gearbox"]),
    ("oil is cooled by fuel",
     ["heat_exchanger", "oil_lines"]),
    ("bleed air is taken off the compressor case",
     ["casing_hpc", "bleed_pipes"]),
    ("turbine cooling air reaches the turbine case",
     ["turbine_cooling_manifold", "casing_turbine"]),
    ("the engine hangs on its mounts",
     ["casing_bypass", "mount_trunnions", "mount_pads"]),
    ("and is steadied at the rear",
     ["casing_turbine", "mount_links_rear"]),
    ("the control unit is wired to the engine",
     ["engine_control", "harnesses", "flange_fan_rear"]),
    ("the fan cowl door is hinged to the case",
     ["fan_cowl_door", "fan_door_hardware", "casing_fan"]),
]


def main():
    parts, collisions, cut_owner, built_by, failures = _joints.load(ROOT, PKG)
    bad = []

    print(f"\n{len(parts)} parts from {len(set(built_by.values()))} modules")

    print("\nMODULES")
    for name, why in failures:
        print(f"  x   {name:26s} did not build: {why}")
        bad.append(f"{name} did not build")
    for key, first, second in collisions:
        print(f"  x   {key:26s} built by both {first} and {second}")
        bad.append(f"{key} is built twice")
    for target, owners in sorted(cut_owner.items()):
        for owner in owners:
            if target not in built_by:
                print(f"  x   {target:26s} cut declared by {owner}, and"
                      f" nothing builds it -- the cutter has no target")
                bad.append(f"{target} cutter from {owner} has no target")
    if not bad:
        print("  ok  every part name is built once, by one module, and every"
              " cutter reaches its target")

    print(f"\nASSEMBLY  (contact within {CONTACT_MM:g} {UNIT})")
    graph = _joints.contact_graph(parts, CONTACT_MM)
    groups = _joints.components(graph)
    main_group = next((g for g in groups if ROOT_PART in g), set())
    loose = [g for g in groups if g is not main_group]
    if not loose:
        print(f"  ok  all {len(main_group)} parts hang together off {ROOT_PART}")
    for g in loose:
        names = ", ".join(sorted(g))
        print(f"  x   detached: {names}")
        bad.append(f"detached: {names}")

    print("\nCIRCUITS")
    for label, chain in CIRCUITS:
        breaks = _joints.broken_links(parts, graph, chain)
        if not breaks:
            print(f"  ok  {label}")
            continue
        for (_i, a, b, why) in breaks:
            extra = ""
            if why == "no contact":
                A, B = _joints.match(parts, a), _joints.match(parts, b)
                d = min(_joints.gap(parts[x], parts[y]) for x in A for y in B)
                extra = f" ({d:.0f} {UNIT} apart)"
            print(f"  x   {label}: {a} -> {b}, {why}{extra}")
            bad.append(f"{label}: {a} -> {b} {why}")

    print()
    if not bad:
        print("PASS  it is one assembly and every circuit is joined")
        return 0
    print(f"FAIL  {len(bad)} joints are not made")
    return 1


if __name__ == "__main__":
    sys.exit(main())
