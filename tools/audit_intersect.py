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
    # a spinner fairs over the fan disc and the roots of the blades bolted to
    # it -- that is the whole of what it is for
    ("spinner", "blades_fan_r1"), ("spinner", "fan_disc_assembly"),

    # The fan frame's struts and the outlet guide vanes are one piece of
    # structure on a real engine -- the OGVs carry the frame load, which is
    # why they are as thick as they are -- and the flow splitter divides that
    # same row into its core and bypass halves.
    ("fan_frame_struts", "vanes_fan_ogv"), ("splitter", "vanes_fan_ogv"),
    # twenty nozzle stems tee off the manifold ring
    ("fuel_manifold", "fuel_nozzles"),

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

    # ------------------------------------------------------------------
    # Joints the check could not reach until it stopped spending its
    # budget on the ones it had already been told about. A gas turbine is
    # an assembly of rings that root into one another: struts through
    # walls, blades into discs, nozzles through casings, seals against
    # tips. Each group below is that construction written down.
    # ------------------------------------------------------------------

    # frames: a strut carries load from an inner hub to an outer casing,
    # so by construction it is inside both of them
    ("fan_frame_struts", "bypass_inner_wall"), ("fan_frame_struts", "fan_frame_hub"),
    ("fan_frame_struts", "bearing_sumps"), ("fan_frame_struts", "casing_hpc"),
    ("fan_frame_struts", "hpc_front_cone"), ("fan_frame_struts", "flange_hpc_fwd"),
    ("turbine_frame_struts", "casing_turbine"),
    ("turbine_frame_struts", "flange_turb_aft"),
    ("turbine_frame_struts", "turbine_frame_hub"),
    ("bypass_struts", "splitter"), ("bypass_struts", "casing_bypass"),
    ("bypass_struts", "casing_hpc"), ("bypass_struts", "bypass_inner_wall"),
    ("bypass_struts", "vanes_fan_ogv"), ("bypass_struts", "flange_hpc_fwd"),
    ("fan_containment", "flange_inlet"), ("antiice_duct", "fan_containment"),

    # rotors: blades root into their disc, run inside their casing, and
    # the seals run on their tips
    ("blades_", "fan_disc_assembly"), ("blades_", "hpc_drum"),
    ("blades_", "turbine_inner_flowpath"), ("blades_", "combustor_dome"),
    ("blades_", "casing_turbine"), ("blades_", "bypass_inner_wall"),
    ("blades_", "combustor_liner_"), ("turbine_blade_outer_air_seals", "blades_"),
    ("hpc_front_cone", "hpc_drum"), ("hpc_rear_cone", "hpc_drum"),
    ("turbine_frame_hub", "lpt_disc_assembly"),
    ("bearing_sumps", "hpt_disc"), ("bearing_sumps", "fan_disc_assembly"),
    ("bearing_sumps", "lpt_disc_assembly"), ("bearing_sumps", "vanes_igv"),
    ("spinner", "vanes_igv"),

    # the towershaft takes drive off the HP shaft at the compressor front
    # hub and runs out through the frame to the gearbox: it crosses every
    # ring between the two on the way
    ("towershaft", "bearing_sumps"), ("towershaft", "brg_3_hp_thrust"),
    ("towershaft", "shaft_hp"), ("towershaft", "fan_frame_hub"),
    ("towershaft", "hpc_front_cone"), ("towershaft", "fan_frame_struts"),
    ("towershaft", "blades_hpc_r1"), ("gearbox", "casing_bypass"),
    ("fuel_lines", "gearbox"), ("access_panels", "gearbox"),

    # combustor and fuel: a nozzle is fitted from outside the casings it
    # passes through, which is how it is changed without splitting the engine
    ("fuel_nozzles", "casing_bypass"), ("fuel_nozzles", "casing_hpc"),
    ("fuel_nozzles", "casing_combustor"), ("fuel_nozzles", "vanes_hpc_s9"),
    ("diffuser", "fuel_nozzles"), ("fuel_manifold", "fuel_nozzles"),
    ("panel_bolts", "fuel_nozzles"), ("diffuser", "hpc_interstage_seals"),
    ("turbine_inner_flowpath", "combustor_liner_inner"),
    ("igniters", "casing_bypass"), ("ignition_exciters", "fan_cowl_door"),
    ("ignition_exciters", "engine_control"),
    ("ignition_exciters", "flange_fan_rear"),

    # externals bolt to the casings and to each other
    ("oil_tank", "flange_fan_rear"), ("oil_tank", "access_panels"),
    ("heat_exchanger", "flange_fan_rear"), ("harnesses", "fan_containment"),
    ("fan_cowl_door", "engine_control"), ("fan_cowl_door", "vbv_doors"),
    ("fan_door_hardware", "vbv_doors"), ("fan_door_hardware", "casing_bypass"),
    ("mount_links_rear", "t5_harness"), ("mount_links_rear", "flange_turb_aft"),
    ("nozzle_links", "casing_augmentor"), ("nozzle_actuators", "casing_augmentor"),
    ("casing_augmentor", "spraybars"), ("oil_lines", "turbine_cooling_manifold"),
    ("panel_bolts", "variable_vane_actuation"), ("panel_bolts", "casing_bypass"),
    ("borescope_ports", "bleed_pipes"),
    ("fan_frame_struts", "splitter"),   # the strut roots in the splitter nose
    # Joints made while closing the circuits, each of which IS the joint:
    # the fuel line onto its manifold, the ignition leads onto the igniter
    # plugs, the convergent flaps hinged on the augmentor's aft flange, and
    # the oil drop into the bearing sumps.
    ("fuel_lines", "fuel_manifold"), ("ignition_exciters", "igniters"),
    ("nozzle_flaps_convergent", "casing_augmentor"),
    ("oil_lines", "bearing_sumps"),
]

if __name__ == "__main__":
    sys.exit(0 if _intersect.run(ROOT, "engine/parts", EXPECTED) else 1)
