# -*- coding: utf-8 -*-
"""Apply adjudication outcomes and test whether field-level conclusions change."""
from __future__ import annotations
import csv, json
from collections import defaultdict
from pathlib import Path
csv.field_size_limit(10**9)
SUP = Path(__file__).resolve().parent.parent / "02_supplement"

dec = list(csv.DictReader(open(SUP/"component_decisions_v7_1400.csv", encoding="utf-8-sig")))
red = list(csv.DictReader(open(SUP/"independent_mechanical_redecode_v8.csv", encoding="utf-8-sig")))

FIELDS = {"exposure": ["unit","eligibility","time_origin","coverage"],
          "follow_up": ["calendar_interval","exposure_qualified_observation","trace_coverage","owner"],
          "closure": ["scope","evidence_basis","date","owner","uncertainty","reopening_rule"]}

# adjudication outcome: candidates I upheld after reading the retained text
UPHELD = [
    ("V25R011","closure","reopening_rule","appellate reversal: High Court upheld the appeal and set aside the judgment"),
    ("V25R025","closure","reopening_rule","appeal process described with its duration and requirements"),
    ("V25R097","closure","reopening_rule","Upper Tribunal granted permission to appeal to the Court of Appeal"),
    ("V25R021","follow_up","calendar_interval","bounded window over which harm events were counted (2000-2013)"),
    ("V25R016","exposure","unit","exposed units named: all hospitals, all students in the matching programme"),
    ("V25R022","exposure","unit","exposed units named: individuals who did not receive the services they needed"),
]
UPHELD_KEYS = {(r, f, c) for r, f, c, _ in UPHELD}

base = defaultdict(dict)      # (record, field) -> {component: status}
for d in dec:
    base[(d["record_id"], d["field"])][d["component"]] = (d["component_status"] == "supported")

cand_keys = {(r["record_id"], r["field"], r["component"]) for r in red
             if r["mechanical_probe_fired"] == "yes" and r["semantic_status"] == "not_recovered"}
upheld_in_pool = {k for k in UPHELD_KEYS if k in cand_keys}

def complete(state, field):
    return all(state.get(c, False) for c in FIELDS[field])

def count_complete(states):
    out = {}
    for f in FIELDS:
        n = sum(1 for (rid, fld), st in states.items() if fld == f and complete(st, f))
        out[f] = n
    return out

# scenario A: no change
A = {k: dict(v) for k, v in base.items()}
# scenario B: + the 6 adjudicated
B = {k: dict(v) for k, v in base.items()}
for (rid, fld, comp) in UPHELD_KEYS:
    B[(rid, fld)][comp] = True
# scenario C: upper bound, all 457 candidates upheld
C = {k: dict(v) for k, v in base.items()}
for (rid, fld, comp) in cand_keys:
    C[(rid, fld)][comp] = True

rowsA, rowsB, rowsC = count_complete(A), count_complete(B), count_complete(C)
tot = lambda s: sum(sum(v.values()) for v in s.values())

print("complete-support rows per field, and total supported component decisions")
print(f"{'field':12s} {'A base':>8s} {'B +6':>8s} {'C +457':>8s}")
for f in FIELDS:
    print(f"{f:12s} {rowsA[f]:8d} {rowsB[f]:8d} {rowsC[f]:8d}")
print()
print("supported decisions: A =", tot(A), " B =", tot(B), " C =", tot(C))
print()
print("candidates in pool:", len(cand_keys))
print("upheld adjudications still present in pool:", len(upheld_in_pool), "of", len(UPHELD_KEYS))
print()
# does any closure row reach 6/6 in scenario B?
for (rid, fld), st in B.items():
    if fld == "closure" and sum(st.values()) >= 5:
        print("  closure row with >=5/6 under B:", rid, {c: st[c] for c in FIELDS['closure']})

json.dump({
 "scenario_A_no_change": {"complete_per_field": rowsA, "supported_decisions": tot(A)},
 "scenario_B_plus_adjudicated": {"complete_per_field": rowsB, "supported_decisions": tot(B),
                                 "additions": [{"record": r, "field": f, "component": c, "reason": why}
                                               for r, f, c, why in UPHELD]},
 "scenario_C_upper_bound": {"complete_per_field": rowsC, "supported_decisions": tot(C)},
 "candidate_pool": len(cand_keys),
}, open(SUP/"adjudication_scenarios_v8.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
print("\nwritten", SUP/"adjudication_scenarios_v8.json")
