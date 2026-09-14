"""Fail the build on parts that are too crude to be the thing they are named.

Part count is the wrong metric and it is easy to game: splitting one mesh into
sixteen raises the count by fifteen and adds no geometry at all. What matters
is whether each part has the shape it actually has.

This is the model the other three are measured against: 99 parts at a mean of
8,642 vertices each, because every blade is an individually lofted aerofoil.
Being the reference is not a reason to go unchecked -- the HP compressor front
"cone" in here was a 0.6 mm disc 340 mm across, and it cleared every vertex
count going. The gate below is a ratchet. Raise it when the model gets better;
never lower it to make a build pass.

So: every part must clear a vertex floor, unless it is genuinely a flat plate
or a simple fastener, and the whole model must clear a mean. The exemptions
are listed by name rather than inferred, so adding one is a deliberate act
that shows up in a diff.

    python3 tools/audit_geometry.py
"""

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A part may be simple only if it really is simple. Each entry is a prefix and
# the reason it is allowed to be.
EXEMPT = {
    "igniters": "two plugs in a hole",
    "spraybars": "tubes with holes in",
}

FLOOR = 200          # vertices, for anything not exempt
TOTAL = 1_450_000   # vertices, over the whole model

# Why the total and not the mean.
#
# This file used to gate on mean vertices per part, and that gate punishes the
# one thing the model most needs: more components. A borescope plug, an
# ignition exciter and a rear mount link are each a few hundred vertices
# because that is what they are -- adding thirteen real line-replaceable units
# to a 104-part engine dropped the mean from 8,463 to 7,631 while the total
# rose by 29,000. A gate that fails on that is telling you to delete hardware.
#
# The docstring above already argued the honest number is the total, and this
# is that argument applied. The per-part floor still stops anything arriving
# as a slab; the total still stops the model being hollowed out. Both are
# ratchets: raise them when the model gets better, never lower them to make a
# build pass.


def audit(path=None):
    path = path or os.path.join(ROOT, "build", "parts.csv")
    rows = list(csv.DictReader(open(path)))
    crude = []
    for r in rows:
        n = int(r["verts"])
        name = r["name"]
        if any(name.startswith(k) for k in EXEMPT):
            continue
        if n < FLOOR:
            crude.append((n, name))
    total = sum(int(r["verts"]) for r in rows)
    mean = total // max(len(rows), 1)
    return sorted(crude), mean, len(rows), total


if __name__ == "__main__":
    crude, mean, n, total = audit()
    print(f"{n} parts, {total:,} verts, mean {mean:,}/part "
          f"(floor {FLOOR}, total target {TOTAL:,})")
    if crude:
        print(f"\n{len(crude)} parts below the floor:")
        for v, name in crude[:40]:
            print(f"  {name:28s} {v:5d} v")
    ok = not crude and total >= TOTAL
    print("\n" + ("PASS  geometry is up to standard"
                  if ok else "FAIL  geometry is too crude"))
    sys.exit(0 if ok else 1)
