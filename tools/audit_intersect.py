"""No part of the engine may occupy another part's space.

    python3 tools/audit_intersect.py            (runs itself under Blender)
    python3 tools/audit_intersect.py --shrink   (after a fix: drop what is fixed)

Every pair of parts whose material overlaps by TOL or more -- measured
exactly, both ways, buried parts included; see tools/_interfere.py -- must be
one of two things:

*   Declared in EXPECTED: meant to be that way, a pin in its bore, a rib inside
    a closed skin. A rule that excuses nothing, or names a part that does not
    exist, fails the audit. A permission that no longer matches anything is a
    hole a regression can fall into unseen, and the list had grown to more
    dead rules than live ones before this was enforced.
*   On the KNOWN list: a real defect, written down with how deep it is and
    where it is. The list only gets shorter. A pair not on it fails, a pair
    that gets deeper fails, and a pair that has been fixed fails until
    --shrink takes it off. --shrink never adds anything.
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
    # ----------------------------------------------------------------
    # The accessory gearbox, joint by joint. Every unit on it -- both
    # generators, both hydraulic pumps, the pressure pump and the scavenge
    # pump -- is bolted to its drive pad through a flange, the gearbox is
    # held to the fan case by its own mounts, and the oil lines run into the
    # pumps and the generator they serve. Each of these overlaps is that
    # fitting. They grew when the accessories stopped being hexagons and got
    # the bolted pads they hang on.
    # ----------------------------------------------------------------
    ("generator_", "gearbox"), ("hydraulic_pump_", "gearbox"),
    ("oil_pressure_pump", "gearbox"), ("oil_scavenge_pump", "gearbox"),
    ("gearbox_mounts", "gearbox"), ("gearbox_mounts", "casing_fan"),
    ("gearbox", "casing_fan"),
    ("oil_lines", "oil_scavenge_pump"), ("oil_lines", "oil_pressure_pump"),
    ("oil_lines", "generator_"),
    # A borescope boss is let into the case and carries the port that
    # threads into it; the aft mount pad bolts to the turbine rear flange;
    # and the fan cowl door passes over the forward mount pad, which is
    # what the hole in a cowl door is for.
    ("borescope_bosses", "casing_bypass"),
    ("borescope_bosses", "borescope_ports"),
    ("mount_pads", "flange_turb_aft"), ("mount_pads", "fan_cowl_door"),
    # A fan frame strut and the bypass strut outboard of it are one radial
    # member built as two parts -- hub to core casing, core casing to fan
    # case -- so they meet at the casing between them.
    ("fan_frame_struts", "bypass_struts"),
    # the T5 rake's harness ring collects eight thermocouple leads and hands
    # them to the engine loom, which is what a harness ring is for
    ("harnesses", "t5_harness"),
    # the control unit's harness ends in a plug mated over its connector
    ("engine_control", "harnesses"),

    # The fan frame's struts and the outlet guide vanes are one piece of
    # structure on a real engine -- the OGVs carry the frame load, which is
    # why they are as thick as they are -- and the flow splitter divides that
    # same row into its core and bypass halves.
    ("fan_frame_struts", "vanes_fan_ogv"),
    # twenty nozzle stems tee off the manifold ring
    ("fuel_manifold", "fuel_nozzles"),

    ("flange_", "casing_"),
    ("flange_", "nozzle_"),
    ("casing_", "casing_"),            # adjacent cans meet at their lands
    ("splitter", "bypass_inner_wall"),

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

    ("fuel_nozzles", "combustor_"),
    ("spraybars", "augmentor_liner"),
    ("flameholder", "augmentor_liner"),
    ("towershaft", "gearbox"),
    ("towershaft", "casing_"),
                # rows overlap where the flowpath does
    ("blades_", "hpc_drum"),
    ("diffuser", "casing_"),
    ("mount_", "casing_"),
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
    # the turbine flowpath inner wall is carried on the disc rims: it is the
    # platform between them, so it shares metal with both discs
    ("hpt_disc", "turbine_inner_flowpath"),
    ("lpt_disc_assembly", "turbine_inner_flowpath"),
    # a variable-vane lever clamps the spindle of the vane it turns, and its
    # unison rings run along the outside of the casing they are mounted to
    ("variable_vane_actuation", "vanes_"),
    ("variable_vane_actuation", "casing_"),
    # a shaft carries its bearings' inner races and its own spool's rotors
    ("shaft_", "brg_"),
    ("shaft_", "hpc_"),

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
    ("blades_", "turbine_inner_flowpath"),
    ("blades_", "bypass_inner_wall"),
    ("blades_", "combustor_liner_"), ("turbine_blade_outer_air_seals", "blades_"),
    ("hpc_front_cone", "hpc_drum"), ("hpc_rear_cone", "hpc_drum"),
    ("centre_body", "vanes_igv"),
    # the fan frame's inner ring -- splitter and core cowl -- is bolted to the
    # HP compressor case's forward flange, under the cowl
    ("casing_hpc", "splitter"),
    ("centre_body", "bearing_sumps"),
    # the No.5 scavenge line leaves through the bottom turbine frame strut:
    # on the engine the strut is hollow and is the line's conduit, and here
    # the struts are solid, so the line is inside one
    ("bearing_sumps", "turbine_frame_struts"),

    # the towershaft takes drive off the HP shaft at the compressor front
    # hub and runs out through the frame to the gearbox: it crosses every
    # ring between the two on the way
    ("towershaft", "bearing_sumps"), ("towershaft", "brg_3_hp_thrust"),
    ("towershaft", "shaft_hp"),
    ("towershaft", "hpc_front_cone"),
    ("towershaft", "blades_hpc_r1"), ("gearbox", "casing_bypass"),
    ("access_panels", "gearbox"),

    # combustor and fuel: a nozzle is fitted from outside the casings it
    # passes through, which is how it is changed without splitting the engine
    ("fuel_nozzles", "casing_bypass"),
    ("fuel_nozzles", "casing_combustor"),
    ("fuel_manifold", "fuel_nozzles"),
    ("turbine_inner_flowpath", "combustor_liner_inner"),
    ("igniters", "casing_bypass"), ("ignition_exciters", "fan_cowl_door"),
    ("ignition_exciters", "engine_control"),
    ("ignition_exciters", "flange_fan_rear"),

    # externals bolt to the casings and to each other
    ("oil_tank", "flange_fan_rear"),
    ("heat_exchanger", "flange_fan_rear"), ("harnesses", "fan_containment"),
    ("fan_cowl_door", "engine_control"), ("fan_cowl_door", "vbv_doors"),
    ("fan_door_hardware", "vbv_doors"), ("fan_door_hardware", "casing_bypass"),
    ("mount_links_rear", "t5_harness"), ("mount_links_rear", "flange_turb_aft"),
    ("nozzle_actuators", "casing_augmentor"),
    ("casing_augmentor", "spraybars"),
    ("panel_bolts", "variable_vane_actuation"), ("panel_bolts", "casing_bypass"),
    ("fan_frame_struts", "splitter"),   # the strut roots in the splitter nose
    # Joints made while closing the circuits, each of which IS the joint:
    # the fuel line onto its manifold, the ignition leads onto the igniter
    # plugs, the convergent flaps hinged on the augmentor's aft flange, and
    # the oil drop into the bearing sumps.
    ("fuel_lines", "fuel_manifold"), ("ignition_exciters", "igniters"),
]

PKG = "engine/parts"
UNIT = 1.0            # mm of real part per model unit
TOL = 0.3            # mm, full size: deeper than this is sharing material

# Real defects, in mm of full-size overlap, deepest first. Each one is a part
# through a part that nobody meant. Fix them and --shrink; never add to it.
# --- KNOWN: rewritten by --shrink, never by hand to add ---
KNOWN = {
    ("bypass_inner_wall", "towershaft"): 63.2,   # at (811.2, 14.2, -476.8)
    ("gearbox", "oil_lines"): 54.8,   # at (570.7, 75.9, -660.2)
    ("fan_cowl_door", "mount_trunnions"): 53.5,   # at (655.9, -342.4, 467.8)
    ("bleed_pipes", "bypass_inner_wall"): 49.3,   # at (1128.2, -387.7, 317.7)
    ("gearbox", "ignition_exciters"): 47.4,   # at (518.0, -11.4, -652.4)
    ("hpc_drum", "towershaft"): 46.6,   # at (820.6, -6.7, -306.8)
    ("bypass_inner_wall", "mount_trunnions"): 45.4,   # at (2520.0, 261.5, 373.5)
    ("flange_turb_aft", "mount_trunnions"): 42.7,   # at (2521.2, 276.3, 398.8)
    ("mount_pads", "mount_trunnions"): 39.5,   # at (2524.9, 274.1, 397.7)
    ("bypass_inner_wall", "turbine_cooling_manifold"): 32.2,   # at (2068.2, 232.8, 395.5)
    ("generator_1", "heat_exchanger"): 32.2,   # at (378.0, 291.0, -612.2)
    ("oil_lines", "towershaft"): 31.8,   # at (768.7, -74.3, -649.0)
    ("bypass_inner_wall", "fuel_nozzles"): 30.4,   # at (1566.0, -440.7, 138.6)
    ("bypass_inner_wall", "igniters"): 29.8,   # at (1673.6, 356.0, 302.0)
    ("mount_trunnions", "vanes_fan_ogv"): 26.8,   # at (681.6, 327.9, 463.8)
    ("access_panels", "towershaft"): 26.7,   # at (800.0, -48.3, -575.1)
    ("harnesses", "ignition_exciters"): 26.4,   # at (1096.1, 58.8, 576.2)
    ("access_panels", "ignition_exciters"): 25.9,   # at (1202.7, 126.9, 549.5)
    ("antiice_duct", "vbv_doors"): 25.6,   # at (761.0, -532.3, -293.7)
    ("flange_fan_rear", "harnesses"): 24.8,   # at (569.0, 204.1, 575.3)
    ("flange_fan_rear", "fuel_lines"): 23.4,   # at (591.0, 417.4, -439.7)
    ("bleed_pipes", "variable_vane_actuation"): 22.1,   # at (986.9, 364.0, -302.1)
    ("bypass_inner_wall", "turbine_frame_struts"): 22.1,   # at (2462.2, 307.1, -320.7)
    ("antiice_duct", "variable_vane_actuation"): 21.5,   # at (-73.0, -554.3, -320.0)
    ("ignition_exciters", "vbv_doors"): 19.8,   # at (766.2, -306.0, -529.8)
    ("antiice_duct", "flange_fan_rear"): 19.0,   # at (591.0, -538.1, -288.2)
    ("access_panels", "variable_vane_actuation"): 18.1,   # at (252.0, -126.2, -593.7)
    ("bypass_inner_wall", "variable_vane_actuation"): 17.5,   # at (884.4, 462.1, -112.1)
    ("casing_combustor", "igniters"): 17.0,   # at (1677.0, -340.4, -299.1)
    ("casing_inlet", "inlet_lip"): 17.0,   # at (-390.0, 575.7, -154.3)
    ("heat_exchanger", "oil_lines"): 16.6,   # at (506.2, 473.1, -421.0)
    ("fan_cowl_door", "flange_fan_rear"): 16.3,   # at (569.0, -75.2, 590.9)
    ("mixer", "turbine_frame_struts"): 15.2,   # at (2520.0, -258.8, 258.8)
    ("harnesses", "vbv_doors"): 14.5,   # at (760.8, 68.8, 604.0)
    ("fuel_lines", "vbv_doors"): 14.1,   # at (730.3, 406.8, -428.5)
    ("oil_lines", "t5_harness"): 13.9,   # at (2460.8, 134.8, -492.2)
    ("harnesses", "turbine_cooling_manifold"): 13.5,   # at (2032.7, 189.5, 501.1)
    ("ignition_exciters", "variable_vane_actuation"): 12.8,   # at (1004.8, -355.7, -482.6)
    ("antiice_duct", "flange_inlet"): 12.5,   # at (10.0, -547.7, -299.2)
    ("harnesses", "variable_vane_actuation"): 12.1,   # at (254.7, 71.6, 627.8)
    ("bypass_inner_wall", "casing_turbine"): 11.8,   # at (1992.0, 393.6, 238.9)
    ("access_panels", "fan_door_hardware"): 10.0,   # at (348.6, -10.5, 600.0)
    ("access_panels", "borescope_ports"): 9.4,   # at (1246.6, 122.8, 542.2)
    ("fan_door_hardware", "ignition_exciters"): 9.1,   # at (502.0, -96.6, 595.7)
    ("flange_hpc_fwd", "towershaft"): 8.9,   # at (768.0, 13.0, -484.6)
    ("borescope_ports", "ignition_exciters"): 8.3,   # at (1236.0, 136.1, 546.4)
    ("engine_control", "fan_door_hardware"): 8.0,   # at (523.0, -440.7, 410.9)
    ("access_panels", "borescope_bosses"): 7.4,   # at (1248.7, 123.7, 542.1)
    ("bypass_inner_wall", "flange_hpc_fwd"): 7.2,   # at (770.0, -355.8, -318.9)
    ("flange_fan_rear", "gearbox"): 7.0,   # at (591.0, 19.8, -605.0)
    ("harnesses", "spraybars"): 6.8,   # at (2809.9, 167.6, 461.3)
    ("hpt_disc", "shaft_hp"): 6.1,   # at (1932.3, 158.3, 0.0)
    ("borescope_bosses", "ignition_exciters"): 6.0,   # at (1237.8, 137.2, 546.4)
    ("bypass_inner_wall", "casing_hpc"): 6.0,   # at (739.0, 440.0, 205.2)
    ("access_panels", "fuel_nozzles"): 5.1,   # at (1584.8, -140.6, -510.6)
    ("access_panels", "turbine_cooling_manifold"): 4.6,   # at (2335.7, 1.8, 506.2)
    ("bleed_pipes", "fuel_nozzles"): 4.4,   # at (1556.0, 421.6, -326.9)
    ("turbine_inner_flowpath", "turbine_interstage_seals"): 3.9,   # at (2115.8, 300.0, 0.0)
    ("casing_fan", "fan_door_hardware"): 3.4,   # at (479.8, 132.9, 579.1)
    ("oil_lines", "oil_tank"): 2.9,   # at (502.0, 562.6, 333.4)
    ("bearing_sumps", "shaft_hp"): 2.4,   # at (2106.0, 92.6, -131.6)
    ("blades_lpt_s2", "lpt_disc_assembly"): 1.4,   # at (2247.2, 254.9, -147.2)
}
# --- end KNOWN ---

if __name__ == "__main__":
    import _interfere
    sys.exit(_interfere.intersect_main(__file__, ROOT, PKG, EXPECTED, KNOWN,
                                       TOL, UNIT))
