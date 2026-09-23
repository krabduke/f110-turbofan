"""Fail the build when a blade row does not fit inside the casing it turns in.

Every other audit here asks whether two parts share space. This one asks the
question a running clearance answers: how much space is left, and is it the
amount the engine was designed to have.

That distinction matters because a clearance fault is not a big overlap. The
last LP turbine rotor's tip finished 0.1 mm outside its casing bore -- a blade
through the case, at 10,000 rpm -- and it passed the intersection audit,
which samples points and cannot see a tenth of a millimetre. What it also
could not see was the opposite fault: the HP compressor's tip clearance ran
from 3.4 mm at the front to 19.5 mm at the back, because the casing was a
straight cone and the flowpath is not. Nothing was touching. It also would
not have compressed anything.

So the casing bore is now derived -- spec.casing_bore pins it to every rotor
tip it passes -- and this is the check that it stayed derived:

  * a rotor holds its running clearance to the bore, within a millimetre and
    a half, at its tightest point;
  * a stator reaches the bore, because its outer platform is the piece of
    bore line the vane hangs from, and stops there;
  * the turbine blade outer air seals sit in the gap between the two, and
    nothing in the rotating assembly crosses a bore anywhere.

    python3 tools/audit_clearance.py
"""

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import _intersect                                      # noqa: E402
import spec                                            # noqa: E402

ROTOR_TOL = 1.5      # mm a rotor may be off its designed running clearance
BAND_MAX = 1.5       # mm a stator platform may stop short of the bore
SPOOL_MIN = 0.0      # mm -- nothing rotating may cross a bore at all

# Rotating hardware that lives in the flowpath and so is checked against the
# bore as well. Anything not listed is either outside the casings or is the
# casing, and is the intersection audit's business rather than this one's.
SPOOL = (
    "fan_disc_assembly", "hpc_drum", "hpc_front_cone",
    "hpc_rear_cone", "hpt_disc", "lpt_disc_assembly",
    "fan_interstage_seals", "hpc_interstage_seals", "turbine_interstage_seals",
    "turbine_blade_outer_air_seals",
)


def _gap(v):
    """Smallest (bore - radius) over a part's vertices, and where it is."""
    worst = None
    for (x, y, z) in v:
        r = math.hypot(y, z)
        cas = spec.enclosing_casing(x, r)
        if cas is None:
            continue
        g = spec.casing_inner(cas, x) - r
        if worst is None or g < worst[0]:
            worst = (g, x, r, cas)
    return worst


def audit():
    parts = _intersect.load_parts(ROOT, "engine/parts")
    bad, checked = [], 0

    for row in spec.all_blade_rows():
        key = f"blades_{row.name}"
        if key not in parts:
            key = f"vanes_{row.name}"
        if key not in parts:
            bad.append((row.name, "row missing from the build"))
            continue
        got = _gap(parts[key][0])
        if got is None:
            bad.append((row.name, "row sits outside every casing"))
            continue
        g = got[0]
        checked += 1
        if row.rotor:
            want = spec.row_standoff(row)
            if abs(g - want) > ROTOR_TOL:
                bad.append((row.name,
                            f"running clearance {g:.2f} mm, designed {want:.1f}"
                            f" (r {got[2]:.1f} at x {got[1]:.0f},"
                            f" {got[3]} bore {got[2] + g:.1f})"))
        else:
            if g < -0.01:
                bad.append((row.name,
                            f"platform {-g:.2f} mm outside the {got[3]} bore"))
            elif g > BAND_MAX:
                bad.append((row.name,
                            f"platform stops {g:.2f} mm short of the"
                            f" {got[3]} bore -- it hangs from nothing"))

    for name in SPOOL:
        if name not in parts:
            bad.append((name, "missing from the build"))
            continue
        got = _gap(parts[name][0])
        if got is None:
            continue
        checked += 1
        if got[0] < SPOOL_MIN:
            bad.append((name,
                        f"{-got[0]:.2f} mm outside the {got[3]} bore"
                        f" (r {got[2]:.1f} at x {got[1]:.0f})"))

    print(f"{checked} rows and rotating assemblies measured against"
          f" {len(spec.CASINGS)} casing bores\n")
    if bad:
        print(f"{len(bad)} do not fit the casing they run in:")
        for name, why in bad:
            print(f"   {name:34s} {why}")
        print("\nFAIL  the flowpath does not clear")
        return 1
    print("PASS  every row holds its clearance and every platform meets"
          " the bore")
    return 0


if __name__ == "__main__":
    sys.exit(audit())
