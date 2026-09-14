"""No part of the engine may occupy another part's space.

    python3 tools/audit_intersect.py
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _intersect

# Pairs that share material on purpose. An engine is an assembly of parts that
# interlock: a bolted flange ring overlaps the casing wall it is bolted to, a
# blade outer air seal is carried in the turbine case, the splitter forms the
# leading edge of the bypass inner wall, and the inlet guide vanes are
# embedded in the case that holds them. Each entry is a deliberate statement
# that the overlap is the assembly, not a mistake.
EXPECTED = [
    ("flange_", "casing_"),
    ("flange_", "inlet_case"),
    ("flange_", "nozzle_"),
    ("casing_", "casing_"),            # adjacent cans meet at their lands
    ("splitter", "bypass_inner_wall"),
    ("splitter", "blades_fan"),
    ("inlet_case", "vanes_igv"),
    ("inlet_case", "inlet_lip"),
    ("turbine_blade_outer_air_seals", "casing_turbine"),
    ("vbv_doors", "casing_bypass"),
    ("access_panels", "casing_"),
    ("panel_bolts", "access_panels"),
    ("fan_containment", "casing_fan"),
    ("bearing_sumps", "fan_frame_hub"),
    ("bearing_sumps", "turbine_frame_hub"),
    ("brg_", "bearing_sumps"),
    ("nozzle_", "nozzle_"),
    ("hpc_interstage_seals", "hpc_drum"),
    ("fan_interstage_seals", "fan_disc_assembly"),
    ("combustor_", "diffuser"),
    ("fuel_nozzles", "combustor_"),
    ("igniters", "combustor_"),
    ("spraybars", "augmentor_liner"),
    ("flameholder", "augmentor_liner"),
    ("towershaft", "gearbox"),
    ("towershaft", "casing_"),
    ("blades_", "vanes_"),             # rows overlap where the flowpath does
    ("blades_", "hpc_drum"),
    ("vanes_", "casing_"),
    ("vanes_", "hpc_drum"),
    ("diffuser", "vanes_"),
    ("diffuser", "casing_"),
    ("mount_", "casing_"),
    ("mount_", "turbine_frame_hub"),
    ("harnesses", "casing_"),
    ("bleed_pipes", "casing_"),
    ("fuel_lines", "casing_"),
    ("oil_lines", "casing_"),
    ("t5_harness", "casing_"),
    ("turbine_cooling_manifold", "casing_"),
    ("borescope_ports", "casing_"),
    ("inlet_probes", "inlet_case"),
    ("inlet_probes", "casing_inlet"),
    ("antiice_duct", "casing_"),
    ("ignition_exciters", "casing_"),
    ("oil_tank", "casing_"),
    ("heat_exchanger", "casing_"),
    ("engine_control", "casing_"),
    ("fan_cowl_door", "casing_"),
    ("fan_door_hardware", "fan_cowl_door"),
    # the flaps hinge on the casing's aft flange, so their forward edge is
    # buried in its last 10 mm -- that is the joint, not a mistake
    ("nozzle_ext_flaps", "casing_augmentor"),
    ("nozzle_actuator_ring", "casing_augmentor"),
    # the turbine flowpath inner wall is carried on the disc rims: it is the
    # platform between them, so it shares metal with both discs
    ("hpt_disc", "turbine_inner_flowpath"),
    ("lpt_disc_assembly", "turbine_inner_flowpath"),
    # a variable-vane lever clamps the spindle of the vane it turns, and its
    # unison rings run along the outside of the casing they are mounted to
    ("variable_vane_actuation", "vanes_"),
    ("variable_vane_actuation", "casing_"),
    ("variable_vane_actuation", "fan_containment"),
    # compressor casing aft flange, diffuser and combustor dome are one
    # bolted joint at station 1600
    ("combustor_dome", "casing_hpc"),
    ("shaft_", "brg_"),
    ("shaft_", "hpc_"),
    ("shaft_", "fan_"),
    ("shaft_", "lpt_"),
    ("shaft_", "turbine_"),
]

if __name__ == "__main__":
    sys.exit(0 if _intersect.run(ROOT, "engine/parts", EXPECTED) else 1)
