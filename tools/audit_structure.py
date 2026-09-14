"""Structural audit for the F110. See tools/_structure.py for the checks.

    python3 tools/audit_structure.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _structure as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CFG = {
    "gap_mm": 0.5,
    "exempt_attached": {},
    "mirror_tol_mm": 1.0,
    "exempt_mirror": {},
    "distinct_tol_mm": 0.5,
    "exempt_distinct": {},
    "exempt_shape": {},

    "singletons": {
        "fan case": (("casing_fan",), 1),
        "spinner": (("spinner",), 1),
        "LP shaft": (("shaft_lp",), 1),
        "HP shaft": (("shaft_hp",), 1),
        "combustor dome": (("combustor_dome",), 1),
        "nozzle actuator ring": (("nozzle_actuator_ring",), 1),
    },

}

if __name__ == "__main__":
    n = S.report(os.path.join(ROOT, "build", "parts.csv"), CFG, "F110")
    sys.exit(0 if n == 0 else 1)
